import logging
import time
import allure
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.api_object_factory.comm_control_policies_factory import CommControlPoliciesFactory
from infra.api.api_object_factory.comm_control_apps_factory import CommControlAppFactory
from infra.api.management_api.user_legacy import UserLegacy, TEMP_PASSWORD, \
    get_user_fields_by_username, is_exists_by_username, DEFAULT_FIRST_NAME, DEFAULT_LAST_NAME, DEFAULT_MAIL, \
    DEFAULT_TITLE
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.api_object_factory.exceptions_factory import ExceptionsFactory
from infra.api.api_object_factory.events_factory import EventsFactory
from infra.api.api_object_factory.rest_collectors_factory import RestCollectorsFactory
from infra.api.api_object_factory.security_policies_factory import SecurityPoliciesFactory
from infra.api.api_object_factory.groups_factory import GroupsFactory

logger = logging.getLogger(__name__)

DEFAULT_REST_API_STATE = 'true'
DEFAULT_REMOTE_SHELL = 'false'
DEFUALT_CUSTOM_SCRIPT = 'false'


class UserRoles(Enum):
    USER = 'User'
    ADMIN = 'Admin'                    # management version 5.2.1>
    LOCAL_ADMIN = 'Local Admin'
    REST_API = 'Rest API'
    IT = 'IT'                          # management version 5.2.1>
    SENIOR_ANALYST = 'Senior Analyst'  # management version 5.2.1>
    ANALYST = 'Analyst'                # management version 5.2.1>
    READ_ONLY = 'Read-Only'            # management version 5.2.1>


LOCAL_ADMIN_ROLES = UserRoles.ADMIN.value


class UserFieldsNames(Enum):
    REST_API = 'restApi'
    ID = 'id'
    USERNAME = 'username'
    ORGANIZATION = 'organization'
    PASSWORD = 'password'
    ROLES = 'roles'
    FIRST_NAME = 'firstName'
    LAST_NAME = 'lastName'
    EMAIL = 'email'
    TITLE = 'title'
    CONFIRM_PASSWORD = 'confirmPassword'
    ROLE = 'role'  # management version 5.2.1>
    CUSTOM_SCRIPT = 'customScript'
    REMOTE_SHELL = 'remoteShell'


class UserRestComponentsFactory:
    """ Create rest factory for each component that is under the user, with the user's auth """
    def __init__(self, organization_name: str, rest_client: RestCommands):
        self.exceptions: ExceptionsFactory = ExceptionsFactory(organization_name=organization_name,
                                                               factory_rest_client=rest_client)
        self.collectors: RestCollectorsFactory = RestCollectorsFactory(organization_name=organization_name,
                                                                       factory_rest_client=rest_client)
        self.events: EventsFactory = EventsFactory(organization_name=organization_name,
                                                   factory_rest_client=rest_client)
        self.security_policies: SecurityPoliciesFactory = SecurityPoliciesFactory(organization_name=organization_name,
                                                                                  factory_rest_client=rest_client)
        self.comm_control_policies: CommControlPoliciesFactory = CommControlPoliciesFactory(
            organization_name=organization_name, factory_rest_client=rest_client)
        self.collector_groups: GroupsFactory = GroupsFactory(organization_name=organization_name,
                                                             factory_rest_client=rest_client)
        self.comm_control_app: CommControlAppFactory = CommControlAppFactory(
            organization_name=organization_name, factory_rest_client=rest_client)


class User(UserLegacy, BaseApiObj):
    """ A wrapper of our internal rest client for working with user capabilities.
    Each user will have its own rest credentials based on user password and name (that passed from users factory)"""

    def __init__(self, password: str, initial_data: dict):
        UserLegacy.__init__(self, password=password, initial_data=initial_data)

    @classmethod
    @allure.step("Create User")
    def create(cls, rest_client: RestCommands, username, user_password, organization_name, roles,
               expected_status_code=200, **optional_data):
        """ Create user with a temp password in order to afterwards to reset to the desired password.
        Reset password in order to avoid "change" password page/logic.
        Optional data: firstName, lastName, email, title """
        assert not is_exists_by_username(rest_client=rest_client, username=username,
                                         organization_name=organization_name), f"User {username} already exists"
        logger.info(f"Create new user '{username}' in organization {organization_name}")
        user_data = {
            UserFieldsNames.USERNAME.value: username,
            UserFieldsNames.PASSWORD.value: TEMP_PASSWORD,
            UserFieldsNames.CONFIRM_PASSWORD.value: TEMP_PASSWORD,
            UserFieldsNames.ROLE.value: roles,
            UserFieldsNames.REST_API.value: DEFAULT_REST_API_STATE,
            UserFieldsNames.FIRST_NAME.value: optional_data.get(UserFieldsNames.FIRST_NAME.value, DEFAULT_FIRST_NAME),
            UserFieldsNames.LAST_NAME.value: optional_data.get(UserFieldsNames.LAST_NAME.value, DEFAULT_LAST_NAME),
            UserFieldsNames.EMAIL.value: optional_data.get(UserFieldsNames.EMAIL.value, DEFAULT_MAIL),
            UserFieldsNames.TITLE.value: optional_data.get(UserFieldsNames.TITLE.value, DEFAULT_TITLE),
            UserFieldsNames.CUSTOM_SCRIPT.value: DEFUALT_CUSTOM_SCRIPT,
            UserFieldsNames.REMOTE_SHELL.value: DEFAULT_REMOTE_SHELL
        }
        rest_client.users_rest.create_user(user_data=user_data,
                                           organization=organization_name,
                                           legacy=False,
                                           expected_status_code=expected_status_code)
        logger.info("Reset to main password and wait until updated")
        rest_client.users_rest.reset_user_password(user_name=username, new_password=user_password,
                                                   organization=organization_name,
                                                   expected_status_code=expected_status_code)
        time.sleep(60)  # For the new password to be valid, 30 is not enough
        new_user_data = get_user_fields_by_username(rest_client=rest_client, username=username,
                                                    organization_name=organization_name, safe=False)
        if expected_status_code == 200:
            user_data[UserFieldsNames.ORGANIZATION.value] = organization_name
            user_data[UserFieldsNames.ROLE.value] = user_data.get(UserFieldsNames.ROLE.value).replace('Admin', 'ROLE_ADMIN')
            _compare_new_user_data(expected_data=user_data, actual_data=new_user_data)
        user = cls(password=user_password, initial_data=new_user_data)
        return user


def _compare_new_user_data(expected_data: dict, actual_data: dict):
    username = expected_data[UserFieldsNames.USERNAME.value]
    logger.info(f"Validate that user {username} created with the correct values as were passed")
    not_relevant_fields = [UserFieldsNames.PASSWORD.value,
                           UserFieldsNames.ROLES.value,
                           UserFieldsNames.CONFIRM_PASSWORD.value]
    for field_name, expected_value in expected_data.items():
        if field_name not in not_relevant_fields:
            actual_value = actual_data[field_name]
            if isinstance(actual_value, bool):
                actual_value = str(actual_value).lower()
                expected_value = expected_value.lower()
            assert actual_value == expected_value, \
                f"User {username} not created successfully: {field_name} is {actual_value} instead of {expected_value}"