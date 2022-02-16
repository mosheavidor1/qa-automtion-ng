import allure
import pytest
from tests.dynamic_content_tests.dynami_content_tests_base import DynamicContentTestsBase


@allure.epic("Management")
@allure.feature("Dynamic content")
@pytest.mark.sanity
class DynamicContentTests(DynamicContentTestsBase):

    @pytest.mark.xray('EN-73362')
    @pytest.mark.testim_sanity
    def test_e2e_exception_dynamic_content(self, management):
        """
        This test run Testim.io for check dynamic content exception
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()
