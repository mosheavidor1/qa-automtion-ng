import allure

from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler
from time import sleep


class ExceptionsTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        Reporter.report("create event")
        self.collector.create_event(malware_name=self.malware_name)
        self.management.rest_ui_client.get_security_events({"process": self.malware_name})

    @allure.step("Run and validate")
    def run_and_validate(self):
        test_name = "Exceptions | Delete all exception"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        test_name = "Security event | Archive all"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Search event"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        test_name = "Exceptions | Delete all exception"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        test_name = "Security event | Archive all"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Search event"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        test_name = "Exceptions | Create exception"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        test_name = "Security event | Archive all"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

        sleep(30)

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Event does not appear"
        self.testim_handler.run_test(test_name=test_name,
                                     data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
