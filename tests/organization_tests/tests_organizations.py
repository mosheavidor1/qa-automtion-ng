import allure
import pytest
from tests.organization_tests.organization_tests_base import OrganizationTestsBase


@allure.story("Organization")
class OrganizationTests(OrganizationTestsBase):

    #@pytest.mark.xray('EN-') #TODO: (yosef) add tiket in Jira
    # @pytest.mark.testim_sanity
    # def test_organization(self, management):
    #     """
    #     This test run Testim.io for check create Organization
    #     """
    #     self.management = management
    #     self.play_test()
    pass
        