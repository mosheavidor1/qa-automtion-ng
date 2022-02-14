from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class SystemEventTestType(Enum):
    TEST_EXPORT_PDF_REPORT = 'TEST_EXPORT_PDF_REPORT'
    TEST_EVENTS_OF_PREVENTION_AND_SIMULATION = 'TEST_EVENTS_OF_PREVENTION_AND_SIMULATION'


class SystemEventTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: SystemEventTestType
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
        if self.test_type == SystemEventTestType.TEST_EXPORT_PDF_REPORT:
            test_name = "System event | export PDF report"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == SystemEventTestType.TEST_EVENTS_OF_PREVENTION_AND_SIMULATION:
            test_name = "system events | prevention simulation"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_event_by_name(self.malware_name)
