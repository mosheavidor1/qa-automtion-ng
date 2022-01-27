import allure

from infra.allure_report_handler.reporter import Reporter
from infra.enums import SystemState
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
import third_party_details
from infra.assertion.assertion import Assertion


class ExceptionBase(BaseTest):

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):

        Reporter.report("create event")
        malware_name = "DynamicCodeTests.exe"
        malware_folder = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\malware_sample'
        target_folder = self.collector.os_station.copy_files_from_shared_folder(self.collector.get_qa_files_path(),
                                                                malware_folder, [malware_name])

        self.collector.os_station.execute_cmd(f'{target_folder}\\{malware_name}', asynchronous=True)

    @allure.step("Run and validate")
    def run_and_validate(self):
        response = self.management.rest_ui_client.get_security_events({'Process': "DynamicCodeTests.exe"})
        if not response:
            assert False, "malware not created"

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name("DynamicCodeTests.exe")

    @allure.step("Validate collector service is running")
    def validate_collector_service_is_running(self, collector):
        if collector.get_collector_status() != SystemState.RUNNING:
            assert False, "Collector service is not running"
