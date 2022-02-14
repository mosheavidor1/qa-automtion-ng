import allure

from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class LDAPTestsBase(BaseTest):
    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()
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

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        test_name = "LDAP | Set LDAP server plus users authentication"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass

