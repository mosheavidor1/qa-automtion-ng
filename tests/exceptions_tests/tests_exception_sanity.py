import allure
import pytest
from tests.exceptions_tests.exceptions_tests_base import ExceptionsTestsBase


@allure.feature("Exceptions")
@pytest.mark.sanity
class ExceptionsTests(ExceptionsTestsBase):

    @pytest.mark.xray('EN-73320')
    @pytest.mark.testim_sanity
    def test_exception_e2e_sanity(self, management):
        """
        This test run Testim.io to check exceptions
        """
        self.management = management
        self.collector = self.management.collectors[1]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()
