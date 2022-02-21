from enum import Enum
import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class FrontendTestType(Enum):
    TEST_NAVIGATION = 'TEST_NAVIGATION'
    TEST_DASHBOARD = 'TEST_DASHBOARD'


class FrontendTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: FrontendTestType
    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == FrontendTestType.TEST_NAVIGATION:
            self.management.ui_client.generic_functionality.ui_navigation(data=self.test_im_params)

        elif self.test_type == FrontendTestType.TEST_DASHBOARD:
            self.management.ui_client.generic_functionality.ui_dashboard(data=self.test_im_params)
