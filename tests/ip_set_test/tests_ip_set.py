import allure
import pytest


@allure.epic("Management")
@allure.feature("IP Set")
class IpSetTests:

    @pytest.mark.xray('EN-73346')
    def test_ip_set(self, management):
        """
        This test run Testim.io
        """
        malware_name = "DynamicCodeTests.exe"
        test_im_params = {"eventName": malware_name}
        management.ui_client.ip_set.set_new_ip_set(data=test_im_params)