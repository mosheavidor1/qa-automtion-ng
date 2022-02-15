import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class IpSetTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        test_name = "IP Set | Set new IP set"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass