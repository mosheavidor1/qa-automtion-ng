from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class FcsTestType(Enum):
    TEST_VULNERABILITY_ON_APPLICATION = 'TEST_VULNERABILITY_ON_APPLICATION'
    TEST_RECLASSIFICATION_ON_SECURITY_EVENT = 'TEST_RECLASSIFICATION_ON_SECURITY_EVENT'


class FcsTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: FcsTestType
    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        Reporter.report("create event")
        self.collector.create_event()
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_ui_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == FcsTestType.TEST_VULNERABILITY_ON_APPLICATION:
            # TODO:(yosef) run aplication with CVE from collector
            test_name = "FCS | Validation connection to FCS by Vulnerability"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == FcsTestType.TEST_RECLASSIFICATION_ON_SECURITY_EVENT:
            test_name = "FCS | Validation connection to FCS by Reclassification"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
