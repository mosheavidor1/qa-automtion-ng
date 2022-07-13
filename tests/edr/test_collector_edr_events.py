import json
import logging
from typing import List

import allure
import pytest


from infra.allure_report_handler.reporter import TEST_STEP, Reporter
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
        jira_xray_handler.management = None
        jira_xray_handler.core = None
        jira_xray_handler.aggregator = None
        jira_xray_handler.collector = collector
        test_status = None
        jira_xray_handler.mark = "EDR_event_tester"

        jira_xray_handler.execution_key = jira_xray_handler.create_test_execution()
        logger.info(f"New test execution created with key '{jira_xray_handler.execution_key}'")

        for test_name, results_dict in test_results_dict.items():

            test_result = results_dict.get('Result')
            if test_result is None:
                logger.info(f"There is no result for {test_name}")
                continue

            ticket_id = results_dict.get('TicketId')
            if ticket_id is None:
                logger.info(f"There is no TicketId for {test_name}")
                continue
                

            match test_result:
                case 'Passed':
                    test_status = TestStatusEnum.PASS
                case 'Failed':
                    test_status = TestStatusEnum.FAIL
                case _: # this it the default
                    continue


            jira_xray_handler.publish_test_result(test_key=ticket_id, status=test_status)

            # logger.info(f"Adding test {single_test_result['TicketId']} ({test})")

        logger.info(f"Execution: {jira_xray_handler.execution_key}")
    else:
        raise Exception(f"Results file is empty, therefore, it not created test execution for the suite.\n"
                        f"{test_results_dict}")


@allure.epic("Collectors")
@allure.feature("EDR events")
@pytest.mark.label("Collectors event tester")
@pytest.mark.edr
@pytest.mark.xray('EN-77708')
def test_edr_events_tester(prepare_working_folder_edr_event_tester,
                           management,
                           collector: CollectorAgent):
    """This test starts EDR simulation which simulates EDR events on Collector side and records it to a json file.
    """

    if isinstance(collector, LinuxCollector):
        assert False, "Currently this test can run only on Windows (Collectors)"

    results_dict = {}
    collector_agent: CollectorAgent = collector

    edr_simulation_path = prepare_working_folder_edr_event_tester

    with TEST_STEP(f"Configure EDR event tester on {collector}:"):
        collector_agent.stop_collector(management.tenant.organization.registration_password)

        logger.info("Running configuration")
        collector_agent.config_edr_simulation_tester(
            simulator_path=edr_simulation_path,
            reg_password=management.tenant.organization.registration_password)

        collector_agent.start_collector()

    with TEST_STEP(f"Start EDR event tester on {collector}:"):
        json_result_file_path, result_filename = collector_agent.start_edr_simulation_tester(
            simulator_path=edr_simulation_path)
        logger.info(fr"Filename for attachment: {result_filename}")

    try:
        results_dict = get_results_json_file_as_dict(collector_agent=collector_agent,
                                                     edr_event_tests_file_path=prepare_working_folder_edr_event_tester,
                                                     result_filename=result_filename,
                                                     json_result_file_path=json_result_file_path)

        Reporter.attach_str_as_json_file(file_name=result_filename, file_content=json.dumps(results_dict))

    except Exception as e:
        Reporter.report("Failed to attach json results file")
        Assertion.add_message_soft_assert(f"Failed to attach json results file, original exception: {e}")

    try:
        report_results_to_jira_xray(collector=collector_agent, test_results_dict=results_dict)
    except Exception as e:
        Reporter.report("Failed to report results to jira")
        Assertion.add_message_soft_assert(f"Failed to report results to jira, original exception: {e}")


