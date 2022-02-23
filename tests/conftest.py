from typing import List

import allure

import sut_details
from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import Assertion
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from infra.system_components.core import Core
from infra.system_components.management import Management
from tests.utils.collectors import CollectorUtils

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
def create_environment_properties_file_for_allure_report():
    alluredir = pytest_config.getoption('--alluredir')
    if alluredir is None:
        return

    management = Management.instance()

    file_path = os.path.join(alluredir, 'environment.properties')
    with open(file_path, 'a+') as f:
        f.write(f'Management IP {management.host_ip}, Version: {management.details.management_version}\r\n')

        for single_aggr in management.aggregators:
            f.write(f'Aggregator IP {single_aggr.host_ip},  Version: {single_aggr.details.version}\r\n')

        for single_core in management.cores:
            f.write(f'Core IP {single_core.details.ip}, Version: {single_core.details.version}\r\n')

        for single_collector in management.collectors:
            os_details = f'Os Name:{single_collector.os_station.os_name}, OS Version: {single_collector.os_station.os_version}, OS Artchitecture: {single_collector.os_station.os_architecture}'
            f.write(f'Collector IP {single_collector.details.ip_address}, Version: {single_collector.get_version()}, OS Details: {os_details}\r\n')


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
        i = item.nodeid.index('[')
        test_key = re.findall(r'prefix_\d+', item.nodeid[i:])
        test_key = test_key[0]
        test_key = test_key.replace('_', '-')
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


@pytest.fixture(scope="function")
def collector(management):
    collector = management.collectors[0]
    CollectorUtils.validate_collector_is_currently_running_according_to_management(management=management,
                                                                                   collector=collector)
    # CollectorUtils.validate_collector_is_currently_running(collector)

    yield collector
    CollectorUtils.validate_collector_is_currently_running_according_to_management(management=management,
                                                                                   collector=collector)
    # CollectorUtils.validate_collector_is_currently_running(collector)


@pytest.fixture(scope="session", autouse=sut_details.debug_mode)
def create_snapshot_for_all_collectors_at_the_beginning_of_the_run(management):
    collectors: List[Collector] = management.collectors
    for single_collector in collectors:
        single_collector.os_station.vm_operations.remove_all_snapshots()
        single_collector.os_station.vm_operations.snapshot_create(snapshot_name=f'beginning_pytest_session_snapshot_{time.time()}')


@pytest.fixture(scope="function", autouse=True)
def validate_all_system_components_are_running(management):
    management.validate_all_system_components_are_running()


@pytest.fixture(scope="function", autouse=True)
def check_if_soft_asserts_were_collected():
    Reporter.report("Nothing to show ath the beginning of the run")
    yield
    Assertion.assert_all()


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def revert_to_snapshot(management):
    revert_to_first_snapshot_for_all_collectors(collectors=management.collectors)
    yield


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def management_logs(management):
    clear_logs_from_management(management=management)
    yield
    append_logs_from_management(management)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def aggregator_logs(management):
    clear_logs_from_all_aggregators(aggregators=management.aggregators)
    yield
    append_logs_from_aggregators(management.aggregators)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def cores_logs(management):
    start_time_dict = get_cores_machine_time(cores=management.cores)
    yield
    append_logs_from_cores(cores=management.cores, initial_time_stamp_dict=start_time_dict)


@pytest.fixture(scope="function", autouse=sut_details.debug_mode)
def collector_logs(management):
    start_time_dict = get_collectors_machine_time(collectors=management.collectors)
    yield
    append_logs_from_collectors(collectors=management.collectors, initial_time_stamp_dict=start_time_dict)


@pytest.fixture(scope="function", autouse=True)
def check_if_collector_has_crashed(management):
    Reporter.report("Nothing to show at the beginning of the run")
    yield
    check_if_collectors_has_crashed(management.collectors)


@allure.step("Clear logs from management")
def clear_logs_from_management(management: Management):
    management.clear_logs()


@allure.step("Clear logs from aggregators")
def clear_logs_from_all_aggregators(aggregators: List[Aggregator]):
    for single_aggr in aggregators:
        single_aggr.clear_logs()


@allure.step("Get cores machine time at the beginning of the test")
def get_cores_machine_time(cores: List[Core]):
    new_dict = {}
    for single_core in cores:
        date_time = single_core.get_current_machine_datetime(date_format="'+%d/%m/%Y %H:%M:%S'")
        new_dict[single_core] = date_time

    return new_dict


@allure.step("Get collectors machine time at the beginning of the test")
def get_collectors_machine_time(collectors: List[Collector]):
    new_dict = {}
    for single_collector in collectors:
        date_time = single_collector.os_station.get_current_machine_datetime(date_format="-UFormat '%d/%m/%Y %T'")
        new_dict[single_collector] = date_time

    return new_dict


@allure.step("Append logs from Management")
def append_logs_from_management(management: Management):
    try:
        management.append_logs_to_report()
    except Exception as e:
        Reporter.report(f"Failed to add logs from management to report, original exception: {str(e)}")


@allure.step("Append logs from Aggregators")
def append_logs_from_aggregators(aggregators: List[Aggregator]):
    for single_aggregator in aggregators:
        try:
            single_aggregator.append_logs_to_report()
        except Exception as e:
            Reporter.report(f"Failed to add logs from aggregator to report, original exception: {str(e)}")


@allure.step("Append logs from cores")
def append_logs_from_cores(cores: List[Core], initial_time_stamp_dict: dict):
    for single_core in cores:
        try:
            time_stamp = initial_time_stamp_dict.get(single_core)
            single_core.append_logs_to_report_by_given_timestamp(first_log_timestamp=time_stamp)
        except Exception as e:
            Reporter.report(f"Failed to add logs from core to report, original exception: {str(e)}")


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


@allure.step("Check if collectors has crashed")
def check_if_collectors_has_crashed(collectors_list):
    crashed_collectors = []
    if collectors_list is not None and len(collectors_list) > 0:
        for single_collector in collectors_list:
            has_crashed = single_collector.has_crash()
            if has_crashed:
                crashed_collectors.append(f'{single_collector}')

        if len(crashed_collectors) > 0:
            assert False, f"Crash was detected in the collectors: {str(crashed_collectors)}"

    else:
        Reporter.report("Collectors list is None, can not check anything")
