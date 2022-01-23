import allure

from infra.allure_report_handler.reporter import Reporter
from infra.enums import SystemState
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
import third_party_details


class ExceptionBase(BaseTest):

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):

        Reporter.report("create event")
        malware_folder = self.collector.copy_malware_to_collector()
        files = self.collector.os_station.get_list_of_files_in_folder(malware_folder)
        if 'DynamicCodeTests.exe' not in files:
            raise Exception(f"malware doesn't exist in collector: {self.collector.os_station.host_ip}")
        self.collector.os_station.execute_cmd(f'{malware_folder}\DynamicCodeTests.exe')

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.rest_ui_client.events.ListEvents(self.collector.os_station.host_ip)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass

    @allure.step("Validate collector service is running")
    def validate_collector_service_is_running(self, collector):
        if collector.get_collector_status() != SystemState.RUNNING:
            assert False, "Collector service is not running"
