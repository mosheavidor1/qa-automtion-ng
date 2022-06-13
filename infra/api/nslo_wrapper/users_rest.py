import json
import logging
from typing import List

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality

logger = logging.getLogger(__name__)


class UsersRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Get users in organization")
    def get_users(self, organization_name: str = None, expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.users.ListUsers(organization=organization_name)
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List users - expected response code: {expected_status_code}, actual: {response.status_code}")

        as_list_of_dicts = json.loads(response.content)
        return as_list_of_dicts

    @allure.step("Create new user")
    def create_user(self, user_data: dict, expected_status_code: int = 200):
        logger.info(f"Create new user with this data :\n {user_data} \n expected: {expected_status_code}")
        status, response = self._rest.users.CreateUser(**user_data)
        # Does response contains data about the new object ????
        err_msg = f"Failed to create user, got {response.status_code} instead of {expected_status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code, error_message=err_msg)

    @allure.step("Update user")
    def update_user(self,
                    user_data,
                    expected_status_code: int = 200):
        status, response = self._rest.users.UpdateUser(username=user_data.username,
                                                       organization=user_data.organization,
                                                       roles=user_data.roles,
                                                       firstName=user_data.firstName,
                                                       lastName=user_data.lastName,
                                                       email=user_data.email,
                                                       title=user_data.title,
                                                       new_username=None)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Update-user - expected response code: {expected_status_code}, actual: {response.status_code}")

    @allure.step("Delete user")
    def delete_user(self,
                    user_name: str,
                    organization: str = None,
                    expected_status_code: int = 200):
        status, response = self._rest.users.DeleteUser(username=user_name,
                                                       organization=organization)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Delete user - expected response code: {expected_status_code}, actual: {response.status_code}")

    @allure.step("Reset user password")
    def reset_user_password(self, user_name: str, new_password: str, organization: str,
                            expected_status_code: int = 200):
        status, response = self._rest.users.ResetPassword(username=user_name,
                                                          password=new_password,
                                                          organization=organization)
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Reset user password - expected response code: {expected_status_code}, actual: {response.status_code}")
