import allure
import pytest


@allure.epic("Management")
@allure.feature("Organization")
class OrganizationTests:

    @pytest.mark.xray('EN-73624')
    def test_create_organization(self, management):
        """
        This test run Testim.io for check create Organization
        """
        test_im_params = {}
        management.ui_client.organizations.create_organization(data=test_im_params)
