from enum import Enum
import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class FrontendTestType(Enum):
    TEST_NAVIGATION = 'TEST_NAVIGATION'
    TEST_DASHBOARD = 'TEST_DASHBOARD'


class FrontendTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: FrontendTestType
    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == FrontendTestType.TEST_NAVIGATION:
            test_name = "UI | Navigation"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == FrontendTestType.TEST_DASHBOARD:
            test_name = "UI | Dashboard"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)
