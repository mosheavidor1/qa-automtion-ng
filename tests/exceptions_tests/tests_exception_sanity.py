import allure
import pytest
from tests.exceptions_tests.exceptions_tests_base import ExceptionsTestsBase, ExceptionTestType


@allure.epic("Management")
@allure.feature("Exception")
@pytest.mark.sanity
@pytest.mark.testim_sanity
class ExceptionsTests(ExceptionsTestsBase):

    @pytest.mark.xray('EN-68889')
    @pytest.mark.testim_sanity
    # Full_covered_exception - event excepted
    def test_create_full_covered_exception(self, management):
        self.test_type = ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-68890')
    @pytest.mark.testim_sanity
    # Partially covered exception - event excepted
    def test_create_partially_covered_exception(self, management):
        self.test_type = ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-68891')
    @pytest.mark.testim_sanity
    # Partially covered exception - event created
    def test_create_partially_covered_exception_event_created(self, management):
        self.test_type = ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-68885')
    @pytest.mark.testim_sanity
    def test_edit_fully_covered_exception(self, management):
        self.test_type = ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

    @pytest.mark.xray('EN-68888')
    @pytest.mark.testim_sanity
    def test_edit_partially_covered_exception(self, management):
        self.test_type = ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION
        self.management = management
        self.collector = self.management.collectors[0]
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
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()
