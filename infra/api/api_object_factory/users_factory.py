from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.management_api.user_legacy import UserLegacy, LOCAL_ADMIN_ROLES_LEGACY
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.user import User, UserFieldsNames, LOCAL_ADMIN_ROLES
import logging
import allure

from infra.utils.utils import StringUtils

logger = logging.getLogger(__name__)


class UsersFactory(BaseApiObjFactory):
    """ Find/Create users in the given organization and return them as rest objects.
    1. The factory's rest credentials will be used only for creating users.
    2. Each user will have its own credentials based on user password and name.
    3. When searching for users we must add the password because the users get api doesn't return the password """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_username(self, username: str, password: str, safe=False):
        """ Find real user by username and return its rest api wrapper with the given password """
        users = self.get_by_field(field_name=UserFieldsNames.USERNAME.value, value=username, password=password)
        if users is None:
            assert safe, f"Org '{self._organization_name}' doesn't contain user {username}"
            logger.debug(f"Org '{self._organization_name}' doesn't contain user {username}")
            return None
        assert len(users) == 1, f"These users have same username ! : \n {users}"
        return users[0]

    def get_by_field(self, field_name, value, password):
        """ Get users by field """
        users = []
        org_name = self._organization_name
        logger.debug(f"Find users with field {field_name} = {value} in org: '{org_name}'")
        all_users_fields = self._factory_rest_client.users_rest.get_users(organization_name=org_name)
        for user_fields in all_users_fields:
            if user_fields[field_name] == value:
                user = User(password=password, initial_data=user_fields)
                users.append(user)
        if len(users):
            logger.debug(f"Found these Users with field {field_name}={value}: \n {users}")
            return users
        logger.debug(f"Users with field {field_name}={value} were not found in {org_name}")
        return None

    @allure.step("Create local admin user - legacy")
    def create_local_admin(self, username, user_password, organization_name,
                           expected_status_code=200,
                           legacy: bool = False, **optional_data) -> User | UserLegacy:
        logger.info(f"Create local admin '{username}' in organization '{organization_name}'")

        if len(user_password) < 15:
            assert False, "User password should contain at least 15 characters"

        assert self._is_str_is_valid_as_password(desired_password=user_password), "User password should " \
                                                                                  "include at least 3 of the cahr " \
                                                                                  "types: uppercase, lower case, " \
                                                                                  "special and numeric"

        if legacy:
            local_admin = UserLegacy.create(rest_client=self._factory_rest_client, username=username,
                                            user_password=user_password,
                                            organization_name=organization_name, roles=LOCAL_ADMIN_ROLES_LEGACY,
                                            expected_status_code=expected_status_code, **optional_data)
        else:
            local_admin = User.create(rest_client=self._factory_rest_client, username=username,
                                      user_password=user_password,
                                      organization_name=organization_name, roles=LOCAL_ADMIN_ROLES,
                                      expected_status_code=expected_status_code, **optional_data)
        return local_admin

    def _is_str_is_valid_as_password(self, desired_password: str) -> bool:
        """
        method that checks if user passowrd is valid according to management restrictions
        :param desired_password: desired password for user
        :return: boolean
        """

        conditions_counter = 0
        if StringUtils.is_str_contains_lower_case_chars(text=desired_password):
            conditions_counter += 1

        if StringUtils.is_str_contains_upper_case_chars(text=desired_password):
            conditions_counter += 1

        if StringUtils.is_str_contains_special_chars(text=desired_password):
            conditions_counter += 1

        if StringUtils.is_str_contains_numeric_chars(text=desired_password):
            conditions_counter += 1

        if conditions_counter < 3:
            return False

        return True
