import allure
import pytest
from tests.LDAP_tests.ldap_test_base import LDAPTestsBase


@allure.epic("Management")
@allure.feature("LDAP")
class LDAPTests(LDAPTestsBase):

    @pytest.mark.xray('EN-73331')
    # @pytest.mark.testim_sanity
    def test_check_LDAP(self, management):
        """
        This test run Testim.io for check LDAP authentication
        """
        self.management = management
        self.play_test()
