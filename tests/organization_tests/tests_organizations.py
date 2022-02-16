import allure
import pytest
from tests.organization_tests.organization_tests_base import OrganizationTestsBase


@allure.epic("Management")
@allure.feature("Organization")
class OrganizationTests(OrganizationTestsBase):

    @pytest.mark.xray('EN-73624')
    @pytest.mark.testim_sanity
    def test_create_organization(self, management):
        """
        This test run Testim.io for check create Organization
        """
        self.management = management
        self.play_test()
