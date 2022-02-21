import allure
import pytest
from tests.frontend_tests.frontend_tests_base import FrontendTestsBase,FrontendTestType


@allure.epic("Management")
@allure.feature("General")
# @pytest.mark.sanity
class FrontendManagementTests(FrontendTestsBase):

    @pytest.mark.xray('EN-73322')
    # @pytest.mark.testim_sanity
    def test_navigation(self, management):
        """
        This test run Testim.io for check the navigation in management
        """
        self.management = management
        self.test_type = FrontendTestType.TEST_NAVIGATION
        self.play_test()

    @pytest.mark.xray('EN-73620')
    # @pytest.mark.testim_sanity
    def test_dashboard(self, management):
        """
        This test run Testim.io
        """
        self.management = management
        self.test_type = FrontendTestType.TEST_DASHBOARD
        self.play_test()


