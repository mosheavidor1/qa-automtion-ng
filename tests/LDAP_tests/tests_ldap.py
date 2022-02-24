import allure
import pytest


@allure.epic("Management")
@allure.feature("LDAP")
class LDAPTests:

    @pytest.mark.xray('EN-73331')
    def test_check_ldap(self, management):
        """
        This test run Testim.io for check LDAP authentication
        """
        test_im_params = {"security_level": "None",
                          "LDAP_host": "10.51.122.21",
                          "Directory_type": "ActiveDirectory",
                          "Bind_User_DN": "CN=domainAccount,CN=Users,DC=automation,DC=com",
                          "Bind_Password": "12345678",
                          "BaseDN": "DC=automation,DC=com",
                          "UserGroupName": "CN=testUserGroup,OU=Groups,OU=QA,DC=automation,DC=com",
                          "LocalAdminGroupName": "CN=testAdminGroup,OU=Groups,OU=QA,DC=automation,DC=com",
                          "AdminGroupName": "CN=testhostergroup,OU=Groups,OU=QA,DC=automation,DC=com"
                          }
        management.ui_client.ldap.set_ldap_server_plus_users_authentication(test_im_params)