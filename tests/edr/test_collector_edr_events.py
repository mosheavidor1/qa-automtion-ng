import json
import logging
import os

import allure
import pytest

from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.system_components.collector import CollectorAgent

logger = logging.getLogger(__name__)


@allure.epic("Collectors")
@allure.feature("EDR events")
@pytest.mark.edr
@pytest.mark.xray('EN-77708')
def test_edr_events_tester(prepare_working_folder_edr_event_tester, management, collector: CollectorAgent):
    """
    This test starts EDR simulation which simulates EDR events on Collector side and records it to a json file.
    """
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
        logger.info(fr"Filename for attachement: {result_filename}")
        
    with TEST_STEP(f"Attaching json file of the results"):
        collector_agent.os_station.wait_for_file_to_appear_in_specified_folder(
            file_path=prepare_working_folder_edr_event_tester,
            file_name=result_filename)

        json_result_file_content = collector_agent.os_station.get_file_content(
            file_path=json_result_file_path)

        Reporter.attach_str_as_json_file(
            file_name=result_filename,
            file_content=json_result_file_content)
