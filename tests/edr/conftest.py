import logging

import allure
import pytest

import sut_details
import third_party_details
from infra.allure_report_handler.reporter import Reporter, INFO
from infra.enums import CollectorTypes
from infra.system_components.collector import CollectorAgent


COLLECTOR_RUNNING_STATE_AFTER_BOOTSTRAP_RESTORED_TIMEOUT = 300
COLLECTOR_STOPPED_STATE_TIMEOUT = 60
COLLECTOR_KEEP_ALIVE_INTERVAL = 5
EDR_EVENT_TESTER_REGISTRATION_PASSWORD = '12345678'
EDR_EVENT_TESTER_RESULTS_PATH = 'Results'

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def prepare_working_folder_edr_event_tester(management, collector: CollectorAgent):
    """
    This preperation is includes multiple procedures:
        * Copy EDR event tester zip file from the network
        * Export it from the file
        * Collector is stopped when going to start the test

    Temporary module installation
    install_specific_module: "python -m pip install pywin32"
    This module is required to be installed before running the tester on a OS stations.
    """
    collector_agent: CollectorAgent = collector

    edr_event_tester_results_path = fr"{third_party_details.SHARED_DRIVE_QA_PATH}\QATools\EdrEventTester\{EDR_EVENT_TESTER_RESULTS_PATH}"
    # edr_event_tester_path = fr"{third_party_details.SHARED_DRIVE_QA_PATH}/QATools/EdrEventTester"
    edr_event_tester_path = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\reference_versions'

    edr_event_tester_file_name = 'eventTester-Win10.zip'

    if sut_details.collector_type == CollectorTypes.WIN_SERVER_2019:
        edr_event_tester_file_name = 'eventTester-WS2019.zip'

    Reporter.report(f"eventTester path: '{edr_event_tester_path}', file name: '{edr_event_tester_file_name}'", INFO)

    Reporter.report("Starting preparation of working edr event tester folder", INFO)
    extracted_path = collector_agent.prepare_edr_event_tester_folder(
        network_path=edr_event_tester_path,
        filename=edr_event_tester_file_name
    )
    Reporter.report(f"extracted path: '{extracted_path}'", INFO)

    results_path_local = collector_agent.os_station.copy_folder_with_files_from_network(
        local_path=fr"{collector_agent.get_qa_files_path()}\{EDR_EVENT_TESTER_RESULTS_PATH}",
        network_path=edr_event_tester_results_path
    )
    backed_up_bootstrap = collector_agent.create_bootstrap_backup(
        reg_password=management.tenant.organization.registration_password
    )

    yield extracted_path, edr_event_tester_results_path

    if sut_details.debug_mode:
        logger.info("Copy results back to network path")
        collector_agent.os_station.copy_folder_with_files_to_network(
            local_path=results_path_local,
            network_path=edr_event_tester_results_path
        )

    collector_agent.restore_bootstrap_file(full_path_filename=backed_up_bootstrap, reg_password=EDR_EVENT_TESTER_REGISTRATION_PASSWORD)

    collector_agent.cleanup_edr_simulation_tester(
        edr_event_tester_path=extracted_path,
        filename=edr_event_tester_file_name)

    collector_agent.wait_until_agent_running(
        timeout_sec=COLLECTOR_RUNNING_STATE_AFTER_BOOTSTRAP_RESTORED_TIMEOUT,
        interval_sec=COLLECTOR_KEEP_ALIVE_INTERVAL)