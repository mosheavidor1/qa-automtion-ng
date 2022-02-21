import allure

from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class ExceptionsTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {}

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        self.test_im_params.update({"eventName": self.malware_name,
                                    "collectorName": str(self.collector.os_station.get_hostname())})
        self.management.ui_client.exceptions.delete_all_exceptions(data=self.test_im_params)

    @allure.step("Run and validate")
    def run_and_validate(self):

        self.management.ui_client.security_policies.set_policies(data=self.test_im_params.update({"securityPolicyMode": "Simulation"}))
        self.management.ui_client.security_events.archive_all()

        self.collector.create_event(malware_name=self.malware_name)

        self.management.ui_client.security_events.check_if_event_in_simulation_block_mode(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_api_client.delete_event_by_name(self.malware_name)
        self.management.ui_client.security_policies.set_policies({"securityPolicyMode": "Prevention"})