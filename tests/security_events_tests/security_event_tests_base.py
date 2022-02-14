from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class SecurityEvantTestType(Enum):
    TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT = 'TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT'
    TEST_SECURITY_EVENT_EXPORT_PDF_REPORT = 'TEST_SECURITY_EVENT_EXPORT_PDF_REPORT'


class SecurityEvantTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: SecurityEvantTestType
    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        Reporter.report("create event")
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_ui_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT:
            test_name = "Security event | export Excel report"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_PDF_REPORT:
            test_name = "Security event | export PDF report"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
