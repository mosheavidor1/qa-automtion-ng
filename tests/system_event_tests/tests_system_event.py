import allure
import pytest
from tests.system_event_tests.system_event_tests_base import SystemEventTestsBase,SystemEventTestType


@allure.story("System event")
class SystemEventTests(SystemEventTestsBase):

    # @pytest.mark.testim_sanity
    # def test_export_PDF_report(self, management):
    #     """
    #     This test run Testim.io for check export PDF report from System event page
    #     """
    #     self.management = management
    #     self.test_type = SystemEventTestType.TEST_EXPORT_PDF_REPORT
    #     self.play_test()
    #
    # @pytest.mark.testim_sanity
    # def test_events_of_prevention_and_simulation(self, management):
    #     """
    #     This test run Testim.io for check that changed mode to simulation or prevention is recorded in system event
    #     """
    #     self.management = management
    #     self.test_type = SystemEventTestType.TEST_EVENTS_OF_PREVENTION_AND_SIMULATION
    #     self.play_test()
    pass