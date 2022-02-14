import time

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler
from time import sleep


class ExceptionsTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {}

    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        self.test_im_params.update({"eventName": self.malware_name,
                                    "collectorName": str(self.collector.os_station.get_hostname())})

        test_name = "Exceptions | Delete all exception"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    @allure.step("Run and validate")
    def run_and_validate(self):

        test_name = "Security policies | Set policies"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params.update({"securityPolicyMode": "Simulation"}))

        test_name = "Security event | Archive all"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | If event in SimulationBlock mode"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
        test_name = "Security policies | Set policies"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params.update({"securityPolicyMode": "Simulation"}))
