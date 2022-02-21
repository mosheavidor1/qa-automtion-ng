import allure

from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from time import sleep


class DynamicContentTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"secUserName": "FortiEDRAdmin",
                      "secUserTitle": "local admin",
                      "secUserFirstName": "first admin",
                      "secUserLastName": "last admin",
                      "secUserEmail": "FortiEDRAdmin@fortinet.com",
                      "secUserPassword": "12345678",
                      "secUserRules": ["Rest API", "Admin", "Local Admin"],
                      "eventName": malware_name}

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_api_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.ui_client.exceptions.delete_all_exceptions(data=self.test_im_params)

        self.management.ui_client.security_events.archive_all(data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        self.management.ui_client.security_events.search_event(data=self.test_im_params)

        self.management.ui_client.dynamic_content.add_exception(data=self.test_im_params)

        self.management.ui_client.security_events.archive_all(self.test_im_params)

        sleep(30)

        self.collector.create_event(malware_name=self.malware_name)

        self.management.ui_client.security_events.event_does_not_appear(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_api_client.delete_event_by_name(self.malware_name)
