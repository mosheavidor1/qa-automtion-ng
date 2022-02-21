from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class SystemEventTestType(Enum):
    TEST_EXPORT_PDF_REPORT = 'TEST_EXPORT_PDF_REPORT'
    TEST_EVENTS_OF_PREVENTION_AND_SIMULATION = 'TEST_EVENTS_OF_PREVENTION_AND_SIMULATION'


class SystemEventTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: SystemEventTestType
    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_api_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == SystemEventTestType.TEST_EXPORT_PDF_REPORT:
            self.management.ui_client.system_events.export_pdf_report(self.test_im_params)

        elif self.test_type == SystemEventTestType.TEST_EVENTS_OF_PREVENTION_AND_SIMULATION:
            self.management.ui_client.system_events.prevention_simulation(self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_api_client.delete_event_by_name(self.malware_name)
