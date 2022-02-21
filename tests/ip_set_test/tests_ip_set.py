import allure
import pytest
from tests.ip_set_test .ip_set_tests_base import IpSetTestsBase


@allure.epic("Management")
@allure.feature("IP Set")
class IpSetTests(IpSetTestsBase):

    @pytest.mark.xray('EN-73346')
    # @pytest.mark.testim_sanity
    def test_ip_set(self, management):
        """
        This test run Testim.io
        """
        self.management = management
        self.play_test()
