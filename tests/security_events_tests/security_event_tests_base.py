from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class SecurityEvantTestType(Enum):
    TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT = 'TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT'
    TEST_SECURITY_EVENT_EXPORT_PDF_REPORT = 'TEST_SECURITY_EVENT_EXPORT_PDF_REPORT'


class SecurityEvantTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: SecurityEvantTestType
    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        Reporter.report("create event")
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_api_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT:
            self.management.ui_client.security_events.export_excel_report(data=self.test_im_params)

        elif self.test_type == SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_PDF_REPORT:
            self.management.ui_client.security_events.export_pdf_report(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_api_client.delete_event_by_name(self.malware_name)
