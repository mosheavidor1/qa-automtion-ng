import allure
import pytest
from tests.fcs_tests.fcs_tests_base import FcsTestsBase, FcsTestType


@allure.epic("Management")
@allure.feature("FCS")
@pytest.mark.sanity
class FcsTests(FcsTestsBase):

    @pytest.mark.xray('EN-73353')
    @pytest.mark.testim_sanity
    def test_vulnerability_on_application(self, management):
        """
        This test run Testim.io for check CVE (Vulnerability)
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.test_type = FcsTestType.TEST_VULNERABILITY_ON_APPLICATION
        self.play_test()

    @pytest.mark.xray('EN-73352')
    @pytest.mark.testim_sanity
    def test_reclassification_on_security_event(self, management):
        """
        This test run Testim.io for check Reclassification
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.test_type = FcsTestType.TEST_RECLASSIFICATION_ON_SECURITY_EVENT
        self.play_test()
