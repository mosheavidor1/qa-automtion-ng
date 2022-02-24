import allure
import pytest


@allure.epic("Management")
@allure.feature("General")
class FrontendManagementTests:

    @pytest.mark.xray('EN-73322')
    def test_navigation(self, management):
        """
        This test run Testim.io for check the navigation in management
        """
        malware_name = "DynamicCodeTests.exe"
        test_im_params = {"eventName": malware_name}
        management.ui_client.generic_functionality.ui_navigation(data=test_im_params)

    @pytest.mark.xray('EN-73620')
    def test_dashboard(self, management):
        """
        This test run Testim.io
        """
        malware_name = "DynamicCodeTests.exe"
        test_im_params = {"eventName": malware_name}
        management.ui_client.generic_functionality.ui_dashboard(data=test_im_params)


