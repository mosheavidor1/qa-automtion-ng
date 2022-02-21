import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class IpSetTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.ui_client.ip_set.set_new_ip_set(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass
