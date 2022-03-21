from typing import List

import allure

import sut_details

from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import Assertion
from infra.enums import CollectorTypes, SystemState
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from infra.system_components.collectors import collectors_common_utils
from infra.system_components.core import Core
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation
from infra.system_components.management import Management
from infra.system_components.system_components_factory import SystemComponentsFactory
from infra.utils.utils import StringUtils

import json
import os
import re
import time
from datetime import datetime

import pytest

from infra.jira_handler.jira_xray_handler import JiraXrayHandler, TestStatusEnum

tests_results = dict()


# consider uncomment it - remove all log file at the beginning of automation run
# @pytest.fixture(scope="session", autouse=True)
# @allure.step("Clear all logs from cores and collectors at the beginning of the run")
# def clear_all_logs_from_cores_and_collectors():
#     management = Management.instance()
#     for single_core in management.cores:
#         single_core.clear_logs()
#
#     for single_collector in management.collectors:
#         single_collector.clear_logs()


@pytest.fixture(scope="session", autouse=True)
@allure.step("Create environment properties file for allure report")
def create_environment_properties_file_for_allure_report(management: Management,
                                                         aggregator: Aggregator,
                                                         core: Core,
                                                         collector: Collector):
    alluredir = pytest_config.getoption('--alluredir')
    if alluredir is None:
        return

    management = Management.instance()

    file_path = os.path.join(alluredir, 'environment.properties')
    with open(file_path, 'a+') as f:
        f.write(f'Management IP {management.host_ip}, Version: {management.details.management_version}\r\n')

        f.write(f'Aggregator IP {aggregator.host_ip},  Version: {aggregator.details.version}\r\n')

        f.write(f'Core IP {core.details.ip}, Version: {core.details.version}\r\n')

        os_details = f'Os Name:{collector.os_station.os_name}, OS Version: {collector.os_station.os_version}, OS Artchitecture: {collector.os_station.os_architecture}'
        f.write(f'Collector IP {collector.details.ip_address}, Version: {collector.get_version()}, OS Details: {os_details}\r\n')


def pytest_configure(config):
    global pytest_config
    pytest_config = config
    if not pytest_config.getoption('--jira-xray'):
        return
    global jira_xray_handler
    mark = pytest_config.getoption('-m')
    jira_xray_handler = JiraXrayHandler(mark=mark, management=Management.instance())


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
            del tests_results['test_path']

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

    if (isinstance(result, dict) and result.get('failed') is True) or (hasattr(result, 'failed') and result.failed is True):
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
    management: Management = Management.instance()
    yield management


@pytest.fixture(scope="session")
def aggregator(management):
    aggregators = SystemComponentsFactory.get_aggregators(management=management)

    if len(aggregators) == 0:
        assert False, "There is no registered aggregator in management, can not create Aggregator object"

    if len(aggregators) > 1:
        assert False, "Automation does not support more than 1 aggregator for functional testing"

    yield aggregators[0]


@pytest.fixture(scope="session")
def core(management):
    cores = SystemComponentsFactory.get_cores(management=management)
    if len(cores) == 0:
        assert False, "There is no registered core in management, can not create Core object"

    if len(cores) > 1:
        assert False, "Automation does not support more than 1 core for functional testing"

    yield cores[0]


@pytest.fixture(scope="session")
def collector(management):
    collector_type = sut_details.collector_type

    if collector_type not in CollectorTypes.__members__:
        assert False, f"Automation does not support collector of the type: {collector_type}"

    collector_type_as_enum = [c_type for c_type in CollectorTypes if c_type.name == collector_type]
    collector_type_as_enum = collector_type_as_enum[0]

    collectors = SystemComponentsFactory.get_collectors(management=management,
                                                        collector_type=collector_type_as_enum)

    if len(collectors) == 0:
        assert False, "There is no registered core in management, can not create Core object"

    # if len(collectors) > 1:
    #     assert False, "Automation does not support more than 1 core for functional testing"

    desired_collector = None
    for collector in collectors:

        if 'windows 10' in collector.os_station.os_name.lower() and \
                collector.os_station.os_architecture == '64-bit'\
                and collector_type_as_enum == CollectorTypes.WINDOWS_10_64:
            desired_collector = collector
            break

        if 'windows 10' in collector.os_station.os_name.lower() and \
                collector.os_station.os_architecture == '32-bit'\
                and collector_type_as_enum == CollectorTypes.WINDOWS_10_32:
            desired_collector = collector
            break

    yield desired_collector


@pytest.fixture(scope="function")
def collector_health_check(collector: Collector):
    assert management.is_collector_status_running_in_mgmt(collector), f"{collector} is not running in {management}"
    # CollectorUtils.validate_collector_is_currently_running(collector)

    yield collector
    assert management.is_collector_status_running_in_mgmt(collector), f"{collector} is not running in {management}"
    # CollectorUtils.validate_collector_is_currently_running(collector)


@pytest.fixture(scope="session", autouse=sut_details.debug_mode)
def create_snapshot_for_all_collectors_at_the_beginning_of_the_run(collector: Collector):
    """
    The role of this method is to create snapshot before the tests start.
    we do it because we revert to this (initial) snapshot before each test start in order to run on "clean"
    collector environment

    :param collector: Collector object
    :return: None
    """
    collector.remove_all_crash_dumps_files()
    collector.os_station.vm_operations.remove_all_snapshots()
    collector.os_station.vm_operations.snapshot_create(snapshot_name=f'beginning_pytest_session_snapshot_{time.time()}')


@pytest.fixture(scope="function", autouse=True)
def validate_all_system_components_are_running(management: Management,
                                               aggregator: Aggregator,
                                               core: Core,
                                               collector: Collector):
    # non collector system components that inherited from fortiEDRLinuxStation
    non_collector_sys_components = [management, aggregator, core]
    collector_status_timeout = 30

    for sys_comp in non_collector_sys_components:
        if isinstance(sys_comp, Core):
            with allure.step("Workaround for core - change DeploymentMethod to Cloud although it's onPrem"):
                content = core.get_file_content(file_path='/opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn')
                deployment_mode = StringUtils.get_txt_by_regex(text=content, regex='"DeploymentMode":"(\w+)"', group=1)
                if deployment_mode == 'OnPremise':
                    core.execute_cmd(
                        """sed -i 's/"DeploymentMode":"OnPremise"/"DeploymentMode":"Cloud"/g' /opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn""")
                    core.stop_service()
                    core.start_service()

        sys_comp.validate_system_component_is_in_desired_state(desired_state=SystemState.RUNNING)

        collectors_common_utils.wait_for_running_collector_status_in_mgmt(management=management,
                                                                          collector=collector,
                                                                          timeout=collector_status_timeout)
        # CollectorUtils.validate_collector_is_currently_running(collector)


@pytest.fixture(scope="function", autouse=True)
def check_if_soft_asserts_were_collected():
    Reporter.report("Nothing to show ath the beginning of the run")
    yield
    Assertion.assert_all()


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def revert_to_snapshot(collector):
    revert_to_first_snapshot_for_all_collectors(collectors=[collector])
    yield


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
    machine_date_format = "%Y-%m-%d %H:%M:%S"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    log_timestamp_date_format_regex = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    log_file_datetime_regex_python = '(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[management],
                                                                 machine_date_format=machine_date_format)
    yield
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[management],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def aggregator_logs(aggregator: Aggregator):

    machine_date_format = "%Y-%m-%d %H:%M:%S"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    log_timestamp_date_format_regex = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    log_file_datetime_regex_python = '(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[aggregator],
                                                                 machine_date_format=machine_date_format)
    yield
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[aggregator],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def cores_logs(core: Core):
    machine_date_format = "%d/%m/%Y %H:%M:%S"
    log_date_format = "%d/%m/%Y %H:%M:%S"
    log_timestamp_date_format_regex = '(0[1-9]|[1-2][0-9]|3[0-1])/(0[1-9]|1[0-2])/[0-9]{4} ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
    log_file_datetime_regex_python = '(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+):(\d+)'

    time_stamps_dict = get_forti_edr_machines_time_stamp_as_dict(forti_edr_stations=[core],
                                                                 machine_date_format=machine_date_format)
    yield
    append_logs_from_forti_edr_linux_station(initial_timestamps_dict=time_stamps_dict,
                                             forti_edr_stations=[core],
                                             machine_timestamp_date_format=machine_date_format,
                                             log_timestamp_date_format=log_date_format,
                                             log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex,
                                             log_file_datetime_regex_python=log_file_datetime_regex_python)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def collector_logs(collector):
    start_time_dict = get_collectors_machine_time(collectors=[collector])
    yield
    append_logs_from_collectors(collectors=[collector], initial_time_stamp_dict=start_time_dict)


@pytest.fixture(scope="session", autouse=False)
def reset_driver_verifier_for_all_collectors(collector: Collector):
    collector.os_station.execute_cmd(cmd='Verifier.exe /reset', fail_on_err=False)
    collector.reboot()


@pytest.fixture(scope="function", autouse=True)
def check_if_collector_has_crashed(collector: Collector):
    Reporter.report("Nothing to show at the beginning of the run")
    yield
    check_if_collectors_has_crashed([collector])


@allure.step("Get collectors machine time at the beginning of the test")
def get_collectors_machine_time(collectors: List[Collector]):
    new_dict = {}
    for single_collector in collectors:
        date_time = single_collector.os_station.get_current_machine_datetime(date_format="-UFormat '%d/%m/%Y %T'")
        new_dict[single_collector] = date_time

    return new_dict


@allure.step("Append logs from collectors")
def append_logs_from_collectors(collectors: List[Collector], initial_time_stamp_dict: dict):
    for single_collector in collectors:
        try:
            time_stamp = initial_time_stamp_dict.get(single_collector)
            single_collector.append_logs_to_report(first_log_timestamp_to_append=time_stamp)
        except Exception as e:
            Reporter.report(f"Failed to add logs from collector to report, original exception: {str(e)}")


@allure.step("Revert all collectors to their snapshot that was taken at the beginning of the run")
def revert_to_first_snapshot_for_all_collectors(collectors: List[Collector]):
    for single_collector in collectors:
        first_snapshot_name = single_collector.os_station.vm_operations.snapshot_list[0][0]
        single_collector.os_station.vm_operations.snapshot_revert_by_name(snapshot_name=first_snapshot_name)
        single_collector.update_process_id()


@allure.step("Check if collectors has crashed")
def check_if_collectors_has_crashed(collectors_list: List[Collector]):
    crashed_collectors = []
    if collectors_list is not None and len(collectors_list) > 0:
        for single_collector in collectors_list:
            has_crashed = single_collector.has_crash()
            if has_crashed:
                crashed_collectors.append(f'{single_collector}')

        if len(crashed_collectors) > 0:
            assert False, f"Crash was detected in the collectors: {str(crashed_collectors)}"

    else:
        assert False, "Didn't pass any collector"


@pytest.fixture()
def xray():
    pass
