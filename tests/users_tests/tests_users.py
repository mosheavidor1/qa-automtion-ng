import allure
import pytest


@allure.epic("Management")
@allure.feature("Users")
class UsersTests:

    @pytest.mark.xray('EN-73630')
    def test_create_all_users_rule_combinations(self, management):
        """
        This test run Testim.io for check creating of users with all combinations of rules
        """
        test_im_params = {}
        management.ui_client.users.create_4_local_users_all_combinations(data=test_im_params)

