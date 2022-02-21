import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class IntegrationTestsBase(BaseTest):

    aggregator: Aggregator = None
    collector: Collector = None

    malware_name = "DynamicCodeTests.exe"
    test_im_params = {}

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.ui_client.connectors.create_custom_connector(data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        self.management.ui_client.security_events.search_archived_event(data=self.test_im_params)

        self.management.ui_client.connectors.check_custom_connector_enforcement(data=self.test_im_params)



    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_api_client.delete_event_by_name(self.malware_name)
