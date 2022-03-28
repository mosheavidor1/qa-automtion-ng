import json
from typing import List

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.containers.management_api_body_containers import UserRestData, CreateUserRestData
from infra.rest.base_rest_functionality import BaseRestFunctionality


class UsersRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Get users")
    def get_users(self,
                  organization: str = None,
                  expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.users.ListUsers(organization=organization)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List users - expected response code: {expected_status_code}, actual: {response.status_code}")

        as_list_of_dicts = json.loads(response.content)
        return as_list_of_dicts

    @allure.step("Create user")
    def create_user(self,
                    user_data: CreateUserRestData,
                    expected_status_code: int = 200):
        status, response = self._rest.users.CreateUser(username=user_data.username,
                                                       organization=user_data.organization,
                                                       password=user_data.password,
                                                       roles=[user_role.value for user_role in user_data.roles],
                                                       firstName=user_data.firstName,
                                                       lastName=user_data.lastName,
                                                       email=user_data.email,
                                                       title=user_data.title)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Create-user - expected response code: {expected_status_code}, actual: {response.status_code}")

    @allure.step("Update user")
    def update_user(self,
                    user_data: UserRestData,
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
