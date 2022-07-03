import uuid
from typing import List
import logging
import allure

import sut_details
from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import Assertion
from infra.enums import CollectorTypes, FortiEdrSystemState, AutomationVmTemplates, \
    CleanVMsReadyForCollectorInstallation
from infra.environment_creation.environment_creation_handler import EnvironmentCreationHandler
from infra.forti_edr_versions_service_handler.forti_edr_versions_service_handler import FortiEdrVersionsServiceHandler
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.core import Core
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation
from infra.system_components.management import Management
from infra.system_components.system_components_factory import SystemComponentsFactory
from infra.utils.utils import StringUtils
from infra.api.api_object_factory.rest_collectors_factory import get_collectors_without_org
from infra.system_components.collectors.collectors_agents_utils import check_if_collectors_has_crashed
import json
import os
import re
import time
from datetime import datetime

import pytest

from infra.jira_handler.jira_xray_handler import JiraXrayHandler, TestStatusEnum
from infra.vpshere.vsphere_cluster_details import ENSILO_VCSA_40
from infra.vpshere.vsphere_utils import VsphereUtils, VsphereClusterHandler
from infra.vpshere.vsphere_vm_operations import VsphereMachineOperations

logger = logging.getLogger(__name__)
tests_results = dict()
jira_xray_handler = JiraXrayHandler()


@pytest.fixture(scope="session", autouse=True)
@allure.step("Create environment properties file for allure report")
def create_environment_properties_file_for_allure_report(management: Management,
                                                         aggregator: Aggregator,
                                                         core: Core,
                                                         collector: CollectorAgent):
    logger.info("Session start - Create environment properties file for allure report")
    alluredir = pytest_config.getoption('--alluredir')
    if alluredir is None:
        return

    file_path = os.path.join(alluredir, 'environment.properties')
    with open(file_path, 'a+') as f:
        f.write(f'Management IP {management.host_ip}, Version: {management.details.management_version}\r\n')

        f.write(f'Aggregator IP {aggregator.host_ip},  Version: {aggregator.details.version}\r\n')

        f.write(f'Core IP {core.details.ip}, Version: {core.details.version}\r\n')

        os_details = f'Os Name:{collector.os_station.os_name}, OS Version: {collector.os_station.os_version}, OS Artchitecture: {collector.os_station.os_architecture}'
        f.write(
            f'Collector IP {collector.os_station.host_ip}, Version: {collector.get_version()}, OS Details: {os_details}\r\n')


@pytest.fixture(scope="session")
def create_service_machine_for_session():
    desired_name = f"{uuid.uuid4().hex[::-5]}__{AutomationVmTemplates.AUTOMATION_SERVICES_MACHINE_TEMPLATE.value}"
    cluster_details = ENSILO_VCSA_40

    logger.info("Creating service VM")
    vm_obj = VsphereUtils.clone_vm_from_template(
        cluster_details=cluster_details,
        template_name=AutomationVmTemplates.AUTOMATION_SERVICES_MACHINE_TEMPLATE,
        desired_name=desired_name)

    yield vm_obj.guest.ipAddress

    cluster_handler = VsphereClusterHandler(cluster_details=cluster_details)
    vm_operations = VsphereMachineOperations(
        service_instance=cluster_handler.service_instance,
        vm_obj=vm_obj)

    logger.info("Remove services VM")
    vm_operations.remove_vm()


def pytest_configure(config):
    global pytest_config
    pytest_config = config
    if not pytest_config.getoption('--jira-xray'):
        return
    global jira_xray_handler
    mark = pytest_config.getoption('-m')
    jira_xray_handler.mark = mark


def pytest_addoption(parser):
    parser.addoption('--jira-xray', action='store_true', help='Upload test results to Jira XRAY')


def pytest_sessionstart(session):
    session.results = dict()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield

    result = outcome.get_result()

    test_path = str(result.nodeid)
    if test_path in tests_results.keys():
        if tests_results[test_path]['hit'] == 3:
            del tests_results[test_path]

    if test_path not in tests_results.keys():
        result = {
            'passed': result.passed,
            'failed': result.failed,
            'skipped': result.skipped,
            'duration': result.duration,
            'outcome': 'passed',
            'hit': 1
        }
        tests_results[test_path] = result

    else:
        tests_results[test_path]['duration'] = result.duration
        tests_results[test_path]['hit'] += 1

        if result.failed is True:
            tests_results[test_path]['passed'] = False
            tests_results[test_path]['failed'] = True

    if (isinstance(result, dict) and result.get('failed') is True) or (
            hasattr(result, 'failed') and result.failed is True):
        if tests_results[test_path]['hit'] == 1:
            tests_results[test_path]['outcome'] = 'skipped'

        elif tests_results[test_path]['hit'] == 2:
            tests_results[test_path][outcome] = 'failed'

    if not pytest_config.getoption('--jira-xray'):
        return

    if item.nodeid.__contains__('['):
        test_key = StringUtils.get_txt_by_regex(text=item.nodeid, regex='(EN-\d+)', group=1)
        if test_key is None:
            return
        test_key = test_key.upper()
    else:
        marker = item.get_closest_marker(name='xray')
        if marker is None:
            return
        test_key = marker.args[0]

    if isinstance(result, dict):
        result_passed = result.get('passed')
        result_failed = result.get('failed')
    else:
        result_passed = result.passed
        result_failed = result.failed

    if call.when is 'call' and result_passed:
        jira_xray_handler.publish_test_result(test_key=test_key, status=TestStatusEnum.PASS)

    elif call.when is 'call' and result_failed:
        jira_xray_handler.publish_test_result(test_key=test_key, status=TestStatusEnum.FAIL)

    elif call.when is 'setup' and result_failed:
        jira_xray_handler.publish_test_result(test_key=test_key, status=TestStatusEnum.ABORTED)

    # in case crash was collected during the run, FAIL will be reported although test might pass
    elif call.when is 'teardown' and result_failed:
        jira_xray_handler.publish_test_result(test_key=test_key, status=TestStatusEnum.FAIL)


def pytest_sessionfinish(session, exitstatus):
    # create_results_json(session, tests_results=tests_results)
    pass


def create_results_json(session, tests_results: dict):
    num_failed_tests = 0
    num_passed_tests = 0
    num_skipped_tests = 0

    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    duration = time.time() - reporter._sessionstarttime
    start_date = str(datetime.fromtimestamp(reporter._sessionstarttime))
    end_date = str(datetime.now())

    single_tests_results_list = []
    for key, value in tests_results.items():
        test_class = None
        test_name = key,
        test_name_splitted = key.split('::')
        if len(test_name_splitted) > 2:
            test_class = test_name_splitted[1]
            test_name = test_name_splitted[2]
        if test_name.__contains__('['):
            i = test_name.index('[')
            issue_id = re.findall('issue_prefix_\d+', test_name[i:])
            if len(issue_id) > 0:
                test_name = f'test_{issue_id[0]}'

        single_result = {
            'test_class': test_class,
            'test_name': test_name,
            'duration': value['duration'],
            'outcome': value['outcome']
        }

        if value['outcome'] == 'passed':
            num_passed_tests += 1

        elif value['outcome'] == 'failed':
            num_failed_tests += 1

        elif value['outcome'] == 'skipped':
            num_skipped_tests += 1

        else:
            pass

        single_tests_results_list.append(single_result)

    results_json_file_path = os.path.join(os.path.abspath(os.path.curdir), '../../results.json')
    with open(results_json_file_path, 'w+') as f:
        # data = f.read()
        f.seek(0)
        # data_as_json = json.loads(data)
        data_as_json = dict()
        data_as_json['start_date'] = start_date
        data_as_json['end_date'] = end_date
        data_as_json['duration'] = duration
        data_as_json['total_fail'] = num_failed_tests
        data_as_json['total_pass'] = num_passed_tests
        data_as_json['total_skip'] = num_skipped_tests
        data_as_json['total_tests'] = num_failed_tests + num_passed_tests + num_skipped_tests
        data_as_json['tests'] = single_tests_results_list

        f.write(json.dumps(data_as_json, indent=4))
        f.truncate()


@pytest.fixture(scope="session")
def management():
    logger.info("Session start - Going to create MGMT instance")
    management: Management = Management.instance()
    logger.info("Management instance was created successfully")

    if sut_details.upgrade_management_to_latest_build:
        management.upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
        management.details.management_version = management.get_version()

    management.wait_until_rest_api_available()

    yield management
    logger.info(f"Session end - Start {management} cleanup validation")
    assert not len(management.temp_tenants), f"{management} still has temp tenants : \n {management.temp_tenants}"


@pytest.fixture(scope="session")
def aggregator(management):
    logger.info("Session start = Going to create Aggregator instance")
    aggregators = SystemComponentsFactory.get_aggregators(management=management)
    logger.info("Aggregator instance was created successfully")

    if len(aggregators) == 0:
        assert False, "There is no registered aggregator in management, can not create Aggregator object"

    if len(aggregators) > 1:
        assert False, "Automation does not support more than 1 aggregator for functional testing"

    aggregator = aggregators[0]
    
    if sut_details.upgrade_aggregator_to_latest_build and management.host_ip != aggregator.host_ip:
        aggregator.upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
        aggregator.details.version = aggregator.get_version()

    yield aggregator


@pytest.fixture(scope="session")
def core(management):
    logger.info("Session start - Going to create Core instance")
    cores = SystemComponentsFactory.get_cores(management=management)
    if len(cores) == 0:
        assert False, "There is no registered core in management, can not create Core object"

    if len(cores) > 1:
        assert False, "Automation does not support more than 1 core for functional testing"

    logger.info("Core instance was created successfully")

    if sut_details.upgrade_core_to_latest_build:
        cores[0].upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
        cores[0].details.version = cores[0].get_version()

    yield cores[0]


@pytest.fixture(scope="session")
def collector(management, aggregator) -> CollectorAgent:
    """ Compound collector agent and move it to the tested organization"""
    logger.info("Session start - Get collector for testing")
    collector_type = sut_details.collector_type
    tenant = management.tenant

    if collector_type not in CollectorTypes.__members__:
        assert False, f"Automation does not support collector agent of the type: {collector_type}"

    collector_type_as_enum = [c_type for c_type in CollectorTypes if c_type.name == collector_type]
    collector_type_as_enum = collector_type_as_enum[0]
    collectors_agents = SystemComponentsFactory.get_collectors_agents(management=management,
                                                                      collector_type=collector_type_as_enum)

    if len(collectors_agents) == 0:
        assert False, f"There are no registered collectors agents of the type {collector_type_as_enum} in management"
    assert len(collectors_agents) == 1, f"We support one agent but actually have these agents: {collectors_agents}"
    collector_agent = collectors_agents[0]
    logger.info(f"Chosen this collector agent for the test: {collector_agent}")
    rest_collector = _find_rest_collector(host_ip=collector_agent.host_ip, tenant=tenant)
    logger.info(f"Rest collector for testing is: {rest_collector}")
    rest_collector = tenant.require_ownership_over_collector(source_collector=rest_collector, safe=True)
    if sut_details.upgrade_collector_latest_build:
        collector_latest_version = get_collector_latest_version(collector=collector_agent)
        if collector_agent.get_version() != collector_latest_version:
            # create snapshot before new version installation process
            create_snapshot_for_collector(snapshot_name=f'snapshot_before_installation_process_{StringUtils.generate_random_string(length=6)}',
                                          management=management,
                                          collector=collector_agent)

            collector_agent.uninstall_collector(registration_password=tenant.organization.registration_password)
            collector_agent.install_collector(version=collector_latest_version, aggregator_ip=aggregator.host_ip,
                                              organization=tenant.organization.get_name(),
                                              registration_password=tenant.organization.registration_password)
            collector_agent.wait_until_agent_running()
            rest_collector.wait_until_running()
    yield collector_agent


def _find_rest_collector(host_ip: str, tenant):
    """ If we start our session from fresh installed env so collector will not be in the tenant.
    But if our session started on not a fresh new env so the collector will be located in the default tenant """

    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=host_ip, safe=True)
    if rest_collector is not None:
        return rest_collector
    else:
        logger.debug(f"{tenant.organization} doesn't contain collector {host_ip}, look in management")
        rest_collectors_without_org = get_collectors_without_org(safe=True)
        assert rest_collectors_without_org is not None, f"Collector {host_ip} was not found at all"
        for rest_collector in rest_collectors_without_org:
            if rest_collector.get_ip(from_cache=True) == host_ip:
                return rest_collector
        assert False, f"Collector {host_ip} was not found"


def _wait_util_rest_collector_appear(host_ip: str, tenant, timeout: int = 60):
    start_time = time.time()
    rest_collector = None
    while time.time() - start_time < timeout and rest_collector is None:
        try:
            rest_collector = _find_rest_collector(host_ip=host_ip, tenant=tenant)
        except:
            time.sleep(1)

    assert rest_collector is not None, f"Can not find the collector with the ip: {host_ip} in the UI within timeout of {timeout} sec"

    return rest_collector


def create_snapshot_for_collector(snapshot_name: str,
                                  management: Management,
                                  collector: CollectorAgent):
    logger.info("Create snapshot for collector")
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    Reporter.report(f"Preparing {collector} for snapshot: stop it + remove old snaps + remove crashes",
                    logger.info)
    Reporter.report("Stop because we want to take snapshot of a collector in a static mode")
    collector.stop_collector(password=management.tenant.organization.registration_password)
    assert collector.is_agent_down(), "Collector agent was not stopped on host"
    rest_collector.wait_until_disconnected()
    collector.os_station.vm_operations.remove_all_snapshots()
    collector.remove_all_crash_dumps_files()
    collector.os_station.vm_operations.snapshot_create(snapshot_name=snapshot_name)
    Reporter.report(f"Snapshot '{snapshot_name}' created")

    Reporter.report("Start the collector so it will be ready for a new test")
    collector.start_collector()
    collector.wait_until_agent_running()
    rest_collector.wait_until_running()
    Reporter.report("Check that starting collector didn't create any crashes (for debugging)")
    check_if_collectors_has_crashed([collector])


@pytest.fixture(scope="session", autouse=sut_details.debug_mode)
def create_snapshot_for_collector_at_the_beginning_of_the_run(management: Management,
                                                              collector: CollectorAgent):
    """
    The role of this method is to create snapshot before the tests start, in static mode (paused).
    we do it because we revert to this (initial) snapshot before each test start in order to run on "clean"
    collector environment.
    Before taking the snapshot we validate that the env is clean (stop collector, no crashes)
    """
    logger.info("Session start - Create snapshot for collector")
    create_snapshot_for_collector(snapshot_name=f'beginning_pytest_session_snapshot_{time.time()}',
                                  management=management,
                                  collector=collector)


# @pytest.fixture(scope="session", autouse=sut_details.upgrade_management_to_latest_build)
# def upgrade_to_latest_build(management: Management,
#                             aggregator: Aggregator,
#                             core: Core,
#                             collector: Collector,
#                             create_snapshot_for_collector_at_the_beginning_of_the_run):
#     """
#     The role of this fixture is to upgrade environment to latest builds.
#     should run after creating snapshot of the system components which gives us the ability to revert in case of
#     upgrade failure or broken version
#     """
#     management.upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
#
#     if management.host_ip != aggregator.host_ip:
#         aggregator.upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
#
#     core.upgrade_to_specific_build(desired_build=None, create_snapshot_before_upgrade=True)
#
#     collector_latest_version = get_collector_latest_version(collector=collector)
#     if collector.get_version() != collector_latest_version:
#         collector.uninstall_collector(registration_password=management.tenant.registration_password)
#         collector.install_collector(version=collector_latest_version,
#                                     aggregator_ip=aggregator.host_ip,
#                                     organization=management.tenant.organization,
#                                     registration_password=management.tenant.registration_password)
#
#         wait_for_running_collector_status_in_cli(collector)
#         wait_for_running_collector_status_in_mgmt(management, collector)
#
#         # in case of installation of the new version passed successfully we need to create new snapshot
#         # for future purposes such as revert to first snapshot (revert to the new version)
#         first_snapshot_name = collector.os_station.vm_operations.snapshot_list[0][0]
#         collector.os_station.vm_operations.remove_all_snapshots()
#         create_snapshot_for_collector(snapshot_name=first_snapshot_name,
#                                       management=management,
#                                       collector=collector)


@pytest.fixture(scope="function", autouse=False)
def revert_to_snapshot(management, collector):
    logger.info("Test start - Revert to collector")
    revert_to_first_snapshot_for_all_collectors(management=management, collectors=[collector])
    yield


@pytest.fixture(scope="function", autouse=True)
def collector_health_check(management: Management, collector: CollectorAgent):
    logger.info(f"Test start - {collector} health check: validate is running")
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    if isinstance(collector, WindowsCollector):
        try:
            collector.os_station.execute_cmd(cmd='echo hi',
                                             return_output=True,
                                             fail_on_err=True,
                                             attach_output_to_report=True,
                                             asynchronous=False)
        except:
            collector.os_station.vm_operations.reboot()
            time.sleep(60)
    assert rest_collector.is_running(), f"{collector} is not running in {management}"
    assert collector.is_agent_running(), f"{collector} status is not running"

    yield collector
    logger.info(f"Test end - {rest_collector} cleanup")
    assert rest_collector.is_running(), f"{collector} is not running in {management}"
    assert collector.is_agent_running(), f"{collector} status is not running"


@pytest.fixture(scope="function", autouse=True)
def validate_all_system_components_are_running(management: Management,
                                               aggregator: Aggregator,
                                               core: Core,
                                               collector: CollectorAgent):
    # non collector system components that inherited from fortiEDRLinuxStation
    logger.info("Test start - Validate that all system components are running")
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    non_collector_sys_components = [management, aggregator, core]
    collector_status_timeout = 30

    for sys_comp in non_collector_sys_components:
    #     if isinstance(sys_comp, Core):
    #         with allure.step("Workaround for core - change DeploymentMethod to Cloud although it's onPrem"):
    #             content = core.get_file_content(file_path='/opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn')
    #             deployment_mode = StringUtils.get_txt_by_regex(text=content, regex='"DeploymentMode":"(\w+)"', group=1)
    #             if deployment_mode == 'OnPremise':
    #                 core.execute_cmd(
    #                     """sed -i 's/"DeploymentMode":"OnPremise"/"DeploymentMode":"Cloud"/g' /opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn""")
    #                 core.stop_service()
    #                 core.start_service()
        sys_comp.validate_system_component_is_in_desired_state(desired_state=FortiEdrSystemState.RUNNING)

    assert rest_collector.is_running(), f"{collector} is not running in {management}"
    Reporter.report(f"Assert that {collector} status is running in CLI")
    assert collector.is_agent_running(), f"{collector} status is not running"


@pytest.fixture(scope="function", autouse=True)
def check_if_soft_asserts_were_collected():
    yield
    logger.info("Test end: Check for soft asserts")
    Assertion.assert_all()


@allure.step("Get machines current time stamps")
def get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations: List[FortiEdrLinuxStation],
                                              machine_date_format):
    new_dict = {}
    for station in forti_edr_stations:
        with allure.step(f"Get {station} current date time"):
            date_time = station.get_current_machine_datetime(date_format=machine_date_format)
            Reporter.report(f"{station} current time stamp is: {date_time}")
            new_dict[station] = date_time

    return new_dict


def append_logs_from_forti_edr_linux_station(initial_timestamps_dict: dict,
                                             forti_edr_stations: List[FortiEdrLinuxStation],
                                             machine_timestamp_date_format,
                                             log_timestamp_date_format,
                                             log_timestamp_date_format_regex_linux,
                                             log_file_datetime_regex_python):
    for station in forti_edr_stations:
        try:
            time_stamp = initial_timestamps_dict.get(station)
            station.append_logs_to_report_by_given_timestamp(first_log_timestamp=time_stamp,
                                                             machine_timestamp_date_format=machine_timestamp_date_format,
                                                             log_timestamp_date_format=log_timestamp_date_format,
                                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex_linux,
                                                             log_file_datetime_regex_python=log_file_datetime_regex_python)
        except Exception as e:
            Reporter.report(f"Failed to add logs from core to report, original exception: {str(e)}")


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def management_logs(management):
    logger.info("Test start - prepare management logs")
    machine_date_format = "%Y-%m-%d %H:%M:%S"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    log_timestamp_date_format_regex = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    log_file_datetime_regex_python = '(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[management],
                                                                 machine_date_format=machine_date_format)
    yield
    logger.info(f"Test end - collect management logs")
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[management],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def aggregator_logs(aggregator: Aggregator):
    logger.info("Test start - prepare aggregator logs")
    machine_date_format = "%Y-%m-%d %H:%M:%S"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    log_timestamp_date_format_regex = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    log_file_datetime_regex_python = '(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[aggregator],
                                                                 machine_date_format=machine_date_format)
    yield
    logger.info(f"Test end - collect aggregator logs")
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[aggregator],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def cores_logs(core: Core):
    logger.info("Test start - prepare core logs")
    machine_date_format = "%d/%m/%Y %H:%M:%S"
    log_date_format = "%d/%m/%Y %H:%M:%S"
    log_timestamp_date_format_regex = '(0[1-9]|[1-2][0-9]|3[0-1])/(0[1-9]|1[0-2])/[0-9]{4} ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
    log_file_datetime_regex_python = '(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[core],
                                                                 machine_date_format=machine_date_format)
    yield
    logger.info("Test end - collect core logs")
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[core],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def collector_logs(collector):
    logger.info("Test start - prepare collector logs")
    start_time_dict = get_collectors_machine_time(collectors=[collector])
    yield
    logger.info("Test end - collect collector logs")
    append_logs_from_collectors(collectors=[collector], initial_time_stamp_dict=start_time_dict)


@pytest.fixture(scope="session", autouse=False)
def reset_driver_verifier_for_all_collectors(collector: CollectorAgent):
    collector.os_station.execute_cmd(cmd='Verifier.exe /reset', fail_on_err=False)
    collector.reboot()


@pytest.fixture(scope="function", autouse=True)
def check_if_collector_has_crashed(collector: CollectorAgent):
    yield
    logger.info("Test end - check if collector has crashes")
    check_if_collectors_has_crashed([collector])


@allure.step("Get collectors machine time at the beginning of the test")
def get_collectors_machine_time(collectors: List[CollectorAgent]):
    new_dict = {}
    for single_collector in collectors:
        date_time = single_collector.os_station.get_current_machine_datetime()
        new_dict[single_collector] = date_time

    return new_dict


@allure.step("Append logs from collectors")
def append_logs_from_collectors(collectors: List[CollectorAgent], initial_time_stamp_dict: dict):
    logger.info("Append logs from collectors")
    for single_collector in collectors:
        try:
            time_stamp = initial_time_stamp_dict.get(single_collector)
            single_collector.append_logs_to_report(first_log_timestamp_to_append=time_stamp)
        except Exception as e:
            Reporter.report(f"Failed to add logs from collector to report, original exception: {str(e)}")


@allure.step("Revert all collectors to their snapshot that was taken at the beginning of the run")
def revert_to_first_snapshot_for_all_collectors(management: Management, collectors: List[CollectorAgent]):
    """ We want to start each test on a clean env(=the first snapshot)
    We also check that the revert operation didn't damage the collector (no crashes)
    """
    wait_after_revert = 10
    for collector in collectors:
        first_snapshot_name = collector.os_station.vm_operations.snapshot_list[0][0]
        collector.os_station.vm_operations.snapshot_revert_by_name(snapshot_name=first_snapshot_name)
        Reporter.report(f"{collector} vm reverted to:'{first_snapshot_name}'", logger.info)
        if isinstance(collector, LinuxCollector):  # To establish new connection after revert
            time.sleep(wait_after_revert)
            collector.os_station.disconnect()
        Reporter.report("Wait until collector is offline in MGMT because it still might be online from previous test",
                        logger.info)
        assert collector.is_agent_down(), "Collector was not stopped"
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        rest_collector.wait_until_disconnected()
        Reporter.report("Sometimes the revert action creates a crash files so we want to remove them",
                        logger.info)
        collector.remove_all_crash_dumps_files()
        Reporter.report("Start the collector so it will be ready for a new test", logger.info)
        collector.start_collector()
        collector.wait_until_agent_running()
        rest_collector.wait_until_running()
        Reporter.report("Check that starting collector didn't create any crashes (for debugging)", logger.info)
        check_if_collectors_has_crashed([collector])


def get_collector_latest_version(collector: CollectorAgent) -> str:
    collector_version = collector.get_version()
    collector_base_version = StringUtils.get_txt_by_regex(text=collector_version, regex='(\d+.\d+.\d+).\d+', group=1)
    latest_versions = FortiEdrVersionsServiceHandler.get_latest_components_builds(base_version=collector_base_version,
                                                                                  num_builds=1)

    latest_version = None
    if isinstance(collector, WindowsCollector):
        architecture = collector.os_station.get_os_architecture()
        if architecture == '64-bit':
            latest_version = latest_versions['windows_64_collector'][0]

        elif architecture == '32-bit':
            latest_version = latest_versions['windows_32_collector'][0]

        else:
            raise Exception(f"Upgrade for windows {architecture} is not supported yet")

    elif isinstance(collector, LinuxCollector):
        if collector.os_station.distro_data.version_name == 'CentOS6':
            latest_version = latest_versions['centos_6_collector'][0]

        elif collector.os_station.distro_data.version_name == 'CentOS7':
            latest_version = latest_versions['centos_7_collector'][0]

        elif collector.os_station.distro_data.version_name == 'CentOS8':
            latest_version = latest_versions['centos_8_collector'][0]

        elif collector.os_station.distro_data.version_name == 'Ubuntu20.04':
            latest_version = latest_versions['ubuntu_20_collector'][0]

        elif 'ubuntu18' in collector.os_station.distro_data.version_name.lower():
            latest_version = latest_versions['ubuntu_18_collector'][0]

        elif 'ubuntu16' in collector.os_station.distro_data.version_name.lower():
            latest_version = latest_versions['ubuntu_16_collector'][0]

        else:
            raise Exception(f"Upgrade for {collector.os_station.distro_data.version_name} is not supported yet")

    assert latest_version is not None, f"Can not find latest version for collector: {collector}"

    return latest_version


@pytest.fixture()
def xray():
    pass


@pytest.fixture(scope="session", autouse=True)
def init_jira_xray_object(management, aggregator, core, collector):
    logger.info("Session start - init jira xray")
    global jira_xray_handler

    jira_xray_handler.management = management
    jira_xray_handler.aggregator = aggregator
    jira_xray_handler.core = core
    jira_xray_handler.collector = collector


######################## dynamic system components fixtures ################################
@pytest.fixture(scope="function")
def dynamic_windows_collector(collector, management, aggregator) -> WindowsCollector:
    vspere_details = ENSILO_VCSA_40
    vsphere_handler = VsphereClusterHandler(vspere_details)
    clean_vms_list = [CleanVMsReadyForCollectorInstallation.WIN_10_32_1,
                      CleanVMsReadyForCollectorInstallation.WIN_10_64_1,
                      CleanVMsReadyForCollectorInstallation.WIN_10_64_2,
                      CleanVMsReadyForCollectorInstallation.WIN_10_64_3,
                      CleanVMsReadyForCollectorInstallation.WIN_11_64_1,
                      CleanVMsReadyForCollectorInstallation.WIN_11_64_2,
                      CleanVMsReadyForCollectorInstallation.WIN_11_64_3,
                      CleanVMsReadyForCollectorInstallation.WIN_SRV_2016_64_1,
                      CleanVMsReadyForCollectorInstallation.WIN_SRV_2019_64_1]

    collector = EnvironmentCreationHandler.add_random_collector_to_setup_from_collectors_pool(
        vsphere_cluster_handler=vsphere_handler,
        clean_vms_list=clean_vms_list,
        version=collector.get_version(),
        aggregator_ip=aggregator.host_ip,
        registration_password=management.registration_password,
        organization=sut_details.default_organization)

    rest_collector = _wait_util_rest_collector_appear(host_ip=collector.host_ip, tenant=management.tenant, timeout=120)
    rest_collector.wait_until_running()

    yield collector

    collector.os_station.vm_operations.revert_to_root_snapshot()
    original_name = collector.os_station.vm_operations.vm_obj.name.replace(EnvironmentCreationHandler.BUSY_VM_COLLECTOR, '')
    collector.os_station.vm_operations.rename_machine_in_vsphere(new_name=original_name)
    collector.os_station.vm_operations.power_off()

    rest_collector = _find_rest_collector(host_ip=collector.host_ip, tenant=management.tenant)
    rest_collector.wait_until_disconnected()
    rest_collector.delete()
