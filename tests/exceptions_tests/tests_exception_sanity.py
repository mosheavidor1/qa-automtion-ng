import allure
import pytest
from tests.exceptions_tests.exceptions_tests_base import ExceptionsTestsBase, ExceptionTestType


@allure.feature("Exceptions")
@pytest.mark.sanity
class ExceptionsTests(ExceptionsTestsBase):

    @pytest.mark.xray('EN-68879')
    def test_create_full_covered_exception(self, management):
        self.test_type = ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[1]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-68884')
    def test_create_partially_covered_exception(self, management):
        self.test_type = ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[1]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-73320')
    @pytest.mark.testim_sanity
    def test_exception_e2e_sanity(self, management):
        """
        This test run Testim.io to check exceptions
        """
        self.test_type = ExceptionTestType.E2E
        self.management = management
        self.collector = self.management.collectors[1]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()