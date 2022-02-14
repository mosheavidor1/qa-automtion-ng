import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class IntegrationTestsBase(BaseTest):

    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    malware_name = "DynamicCodeTests.exe"
    test_im_params = {}

    @allure.step("Run and validate")
    def run_and_validate(self):
        test_name = "connectors | create custom connector"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Search Archived event"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        test_name = "Connectors | Check custom connector enforcement"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
