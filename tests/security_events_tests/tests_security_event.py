import allure
import pytest
from tests.security_events_tests.security_event_tests_base import SecurityEvantTestsBase, SecurityEvantTestType


@allure.epic("Management")
@allure.feature("Security Events")
class SecurityEventTests(SecurityEvantTestsBase):

    @pytest.mark.xray('EN-73626')
    @pytest.mark.testim_sanity
    def test_security_event_export_excel_report(self, management):
        """
        This test run Testim.io for export Excel report from event viewer page
        """
        self.test_type = SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_EXCEL_REPORT
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-73627')
    @pytest.mark.testim_sanity
    def test_security_event_export_PDF_report(self, management):
        """
        This test run Testim.io for export PDF report from event viewer page
        """
        self.test_type = SecurityEvantTestType.TEST_SECURITY_EVENT_EXPORT_PDF_REPORT
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()
