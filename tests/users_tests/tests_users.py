import allure
import pytest
from tests.users_tests.users_test_base import UsersTestsBase


@allure.epic("Management")
@allure.feature("Users")
class UsersTests(UsersTestsBase):

    @pytest.mark.xray('EN-73630')
    @pytest.mark.testim_sanity
    def test_create_all_users_rule_combinations(self, management):
        """
        This test run Testim.io for check creating of users with all combinations of rules
        """
        self.management = management
        self.play_test()

