import json
import logging

import allure
import pytest


from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.assertion.assertion import Assertion
from infra.jira_handler.jira_xray_handler import JiraXrayHandler, TestStatusEnum
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector

logger = logging.getLogger(__name__)


@allure.step(f"Get results json dict")
def get_results_json_file_as_dict(collector_agent: CollectorAgent,
                                  edr_event_tests_file_path: str,
                                  result_filename: str,
                                  json_result_file_path: str) -> dict:
    collector_agent.os_station.wait_for_file_to_appear_in_specified_folder(
        file_path=edr_event_tests_file_path,
        file_name=result_filename)

    json_result_file_content = collector_agent.os_station.get_file_content(
        file_path=json_result_file_path)

    try:
        json_content_dict = json.loads(json_result_file_content)
    except:
        assert False, "Can not parse the json result file from some reason, please check it"

    assert len(json_content_dict) > 0, "No results found in the result file"

    return json_content_dict


@allure.step("Report results to jira xray")
def report_results_to_jira_xray(collector: CollectorAgent, test_results_dict: dict):
    """Create a new test execution for the given tests results file.
    the fixture passes the test results from file as dictionary and adds all the tests to the created execution.
    """

    if len(test_results_dict) > 0:

        jira_xray_handler = JiraXrayHandler()
        jira_xray_handler.management_version = None
        jira_xray_handler.core_version = None

        try:
            jira_xray_handler.collector_version = collector.get_version()
            jira_xray_handler.collector_os_name = collector.os_station.os_name
            jira_xray_handler.collector_os_architecture = collector.os_station.os_architecture
            jira_xray_handler.collector_os_version = collector.os_station.os_version
        except Exception as e:
            assert False, r"Failed to extract collector info since something is wrong " \
                          "with connectivity to it, original exception is: {e}"
        test_status = None
        jira_xray_handler.mark = "EDR_event_tester"

        jira_xray_handler.execution_key = jira_xray_handler.create_test_execution()
        Reporter.report(f"New test execution created: http://jira.ensilo.local/browse/{jira_xray_handler.execution_key}", INFO)

        for test_name, results_dict in test_results_dict.items():

            test_result = results_dict.get('Result')
            if test_result is None:
                logger.info(f"There is no result for {test_name}")
                continue

            ticket_id = results_dict.get('TicketId')
            if ticket_id is None:
                logger.info(f"There is no TicketId for {test_name}")
                continue

            if test_result == 'Passed':
                test_status = TestStatusEnum.PASS
            elif test_result == 'Failed':
                test_status = TestStatusEnum.FAIL
            else:
                continue

            jira_xray_handler.publish_test_result(test_key=ticket_id, status=test_status)

        logger.info(f"Execution: {jira_xray_handler.execution_key}")
        allure.link(url=f'http://jira.ensilo.local/browse/{jira_xray_handler.execution_key}', name="Jira execution")
    else:
        raise Exception(f"Results file is empty, therefore, it not created test execution for the suite.\n"
                        f"{test_results_dict}")


def attaching_files_to_the_report(
        collector: CollectorAgent,
        extracted_path: str,
        result_filename: str,
        json_result_file_path: str
        ):
    try:
        results_dict = get_results_json_file_as_dict(
            collector_agent=collector,
            edr_event_tests_file_path=extracted_path,
            result_filename=result_filename,
            json_result_file_path=json_result_file_path
        )
        assert len(results_dict) > 0, f"No results in the file: '{results_dict}'"

        Reporter.attach_str_as_json_file(
            file_name=result_filename,
            file_content=json.dumps(results_dict, indent=2)
        )
        log_files_list = collector.os_station.get_list_of_files_in_folder(
            folder_path=extracted_path,
            file_suffix='.log'
        )

        for file in log_files_list:
            file_content = collector.os_station.get_file_content(file_path=file)

            logger.info(fr"Adding file to report: {file}")
            Reporter.attach_str_as_file(
                file_name=file,
                file_content=file_content
            )
    except Exception as e:
        Reporter.report("Failed to attach file to the report")
        Assertion.add_message_soft_assert(f"Failed to attach file to the report, original exception: {e}")

@allure.epic("Collectors")
@allure.feature("EDR events")
@pytest.mark.label("Collectors event tester")
@pytest.mark.edr
@pytest.mark.xray('EN-77708')
def test_edr_events_tester(prepare_working_folder_edr_event_tester,
                           management,
                           collector: CollectorAgent):
    """
    It runs the EDR event tester on the collector

    :param prepare_working_folder_edr_event_tester: This is a fixture that will be called before the test. It will download
    the EDR event tester, extract it, and return the path to the extracted folder
    :param management: The management object
    :param collector: CollectorAgent - this is the collector agent object
    :type collector: CollectorAgent
    """

    if isinstance(collector, LinuxCollector):
        assert False, "Currently this test can run only on Windows (Collectors)"

    results_dict = {}
    collector_agent: CollectorAgent = collector

    extracted_path, edr_event_tester_results_path = prepare_working_folder_edr_event_tester

    with TEST_STEP(f"Configure EDR event tester on '{collector}'"):

        logger.info("Running configuration")
        collector_agent.config_edr_simulation_tester(
            simulator_path=extracted_path,
            reg_password=management.tenant.organization.registration_password)

        collector_agent.start_collector()

    with TEST_STEP(f"Start EDR event tester on '{collector}'"):
        json_result_file_path, result_filename = collector_agent.start_edr_simulation_tester(
            collector=collector_agent,
            simulator_path=extracted_path)

        logger.info(fr"Filename for attachment: '{result_filename}'")
        if len(collector_agent.os_station.get_list_of_files_in_folder(extracted_path, result_filename)) == 0:
            assert False, "Could not find result file"
    with TEST_STEP(f"Attaching files"):

        try:
            results_dict = get_results_json_file_as_dict(
                collector_agent=collector_agent,
                edr_event_tests_file_path=extracted_path,
                result_filename=result_filename,
                json_result_file_path=json_result_file_path
            )
            assert len(results_dict) > 0, f"No results in the file: '{results_dict}'"

            Reporter.attach_str_as_json_file(
                file_name=result_filename,
                file_content=json.dumps(results_dict, indent=2)
            )
        except Exception as e:
            Reporter.report("Failed to attach file to the report")
            Assertion.add_message_soft_assert(f"Failed to attach file to the report, original exception: {e}")

    try:
        execution_id = report_results_to_jira_xray(collector=collector_agent, test_results_dict=results_dict)
    except Exception as e:
        Reporter.report("Failed to report results to jira")
        Assertion.add_message_soft_assert(f"Failed to report results to jira, original exception: {e}")