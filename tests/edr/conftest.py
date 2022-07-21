import logging

import pytest

import third_party_details
from infra.system_components.collector import CollectorAgent


COLLECTOR_RUNNING_STATE_AFTER_BOOTSTRAP_RESTORED_TIMEOUT = 180
COLLECTOR_STOPPED_STATE_TIMEOUT = 60
COLLECTOR_KEEP_ALIVE_INTERVAL = 5
EDR_EVENT_TESTER_REGISTRATION_PASSWORD = '12345678'

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def prepare_working_folder_edr_event_tester(management, collector: CollectorAgent):
    """
    This preperation is includes multiple procedures:
        * Copy EDR event tester zip file from the network
        * Export it from the file
        * Collector is stopped when going to start the test
    """
    collector_agent: CollectorAgent = collector

    # edr_event_tester_path = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\QATools\EdrEventTester'
    # edr_event_tester_file_name = 'eventTester.zip'

    edr_event_tester_path = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\reference_versions'
    edr_event_tester_file_name = 'eventTester-v1.zip'
    logger.debug(f"eventTester path: {edr_event_tester_path}, file name: {edr_event_tester_file_name}")

    logger.info("Starting preparation of working edr event tester folder")
    extracted_path = collector_agent.prepare_edr_event_tester_folder(
        network_path=edr_event_tester_path,
        filename=edr_event_tester_file_name)
    logger.debug(f"extracted path: {extracted_path}")

    backed_up_bootstrap = collector_agent.create_bootstrap_backup(
        reg_password=management.tenant.organization.registration_password)

    yield extracted_path

    logger.debug(f"Stopping collector with password '{EDR_EVENT_TESTER_REGISTRATION_PASSWORD}'")
    collector_agent.stop_collector(password=EDR_EVENT_TESTER_REGISTRATION_PASSWORD)

    logger.info("Restoring bootstrap file")
    collector_agent.restore_bootstrap_file(full_path_filename=backed_up_bootstrap)

    collector_agent.cleanup_edr_simulation_tester(
        edr_event_tester_path=extracted_path,
        filename=edr_event_tester_file_name)

    logger.info("Starting collector")
    collector_agent.start_collector()

    collector_agent.wait_until_agent_running(
        timeout_sec=COLLECTOR_RUNNING_STATE_AFTER_BOOTSTRAP_RESTORED_TIMEOUT,
        interval_sec=COLLECTOR_KEEP_ALIVE_INTERVAL)