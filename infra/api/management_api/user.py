import logging
import time
import allure
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.api_object_factory.comm_control_policies_factory import CommControlPoliciesFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.api_object_factory.exceptions_factory import ExceptionsFactory
from infra.api.api_object_factory.events_factory import EventsFactory
from infra.api.api_object_factory.rest_collectors_factory import RestCollectorsFactory
from infra.api.api_object_factory.security_policies_factory import SecurityPoliciesFactory
from infra.api.api_object_factory.groups_factory import GroupsFactory
import sut_details

logger = logging.getLogger(__name__)

DEFAULT_MAIL = "user@ensilo.com"
DEFAULT_FIRST_NAME = 'firstname'
DEFAULT_LAST_NAME = 'lastname'
DEFAULT_TITLE = "title"
TEMP_PASSWORD = "test1234567"
DEFAULT_PASSWORD = f"{TEMP_PASSWORD}_1"


class UserRoles(Enum):
    USER = 'User'
    ADMIN = 'Admin'
    LOCAL_ADMIN = 'Local Admin'
    REST_API = 'Rest API'


LOCAL_ADMIN_ROLES = [UserRoles.USER.value, UserRoles.LOCAL_ADMIN.value, UserRoles.REST_API.value]


class UserFieldsNames(Enum):
    ID = 'id'
    USERNAME = 'username'
    ORGANIZATION = 'organization'
    PASSWORD = 'password'
    ROLES = 'roles'
    FIRST_NAME = 'firstName'
    LAST_NAME = 'lastName'
    EMAIL = 'email'
    TITLE = 'title'


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


class User(BaseApiObj):
    """ A wrapper of our internal rest client for working with user capabilities.
    Each user will have its own rest credentials based on user password and name (that passed from users factory)"""

    def __init__(self, password: str, initial_data: dict):
        self._password = password
        self._id = initial_data[UserFieldsNames.ID.value]  # Static, unique identifier
        self._organization_name = initial_data[UserFieldsNames.ORGANIZATION.value]
        super().__init__(rest_client=RestCommands(management_ip=sut_details.management_host,
                                                  management_user=initial_data[UserFieldsNames.USERNAME.value],
                                                  management_password=self._password,
                                                  organization=self._organization_name),
                         initial_data=initial_data)
        self._rest_components = UserRestComponentsFactory(organization_name=self._organization_name,
                                                          rest_client=self._rest_client)

    @property
    def id(self) -> int:
        return self._id

    @property
    def rest_components(self) -> UserRestComponentsFactory:
        """ Factory for creating/finding user's components like exceptions, collectors, etc.
            With the user's rest credentials """
        return self._rest_components

    @property
    def password(self) -> str:
        """ Need to maintain password because nslo post/get user api response doesn't contain the password """
        return self._password

    @property
    def organization_name(self) -> str:
        """ Need to maintain organization name because nslo get users api can be queried only with organization name,
        can't do it with user id. """
        return self._organization_name

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
            UserFieldsNames.ORGANIZATION.value: organization_name,
            UserFieldsNames.PASSWORD.value: TEMP_PASSWORD,
            UserFieldsNames.ROLES.value: roles,
            UserFieldsNames.FIRST_NAME.value: optional_data.get(UserFieldsNames.FIRST_NAME.value, DEFAULT_FIRST_NAME),
            UserFieldsNames.LAST_NAME.value: optional_data.get(UserFieldsNames.LAST_NAME.value, DEFAULT_LAST_NAME),
            UserFieldsNames.EMAIL.value: optional_data.get(UserFieldsNames.EMAIL.value, DEFAULT_MAIL),
            UserFieldsNames.TITLE.value: optional_data.get(UserFieldsNames.TITLE.value, DEFAULT_TITLE)
        }
        rest_client.users_rest.create_user(user_data=user_data, expected_status_code=expected_status_code)
        logger.info("Reset to main password and wait until updated")
        rest_client.users_rest.reset_user_password(user_name=username, new_password=user_password,
                                                   organization=organization_name,
                                                   expected_status_code=expected_status_code)
        time.sleep(60)  # For the new password to be valid, 30 is not enougth
        new_user_data = get_user_fields_by_username(rest_client=rest_client, username=username,
                                                    organization_name=organization_name, safe=False)
        if expected_status_code == 200:
            _compare_new_user_data(expected_data=user_data, actual_data=new_user_data)
        user = cls(password=user_password, initial_data=new_user_data)
        return user

    def get_username(self, from_cache=None, update_cache=True):
        field_name = UserFieldsNames.USERNAME.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def _get_field(self, field_name, from_cache, update_cache):
        from_cache = from_cache if from_cache is not None else self._use_cache
        if from_cache:
            value = self._cache[field_name]
        else:
            updated_value = self.get_fields()[field_name]
            value = updated_value
            if update_cache:
                self._cache[field_name] = updated_value
        return value

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        users_fields = rest_client.users_rest.get_users(organization_name=self.organization_name)
        for user_fields in users_fields:
            if user_fields[UserFieldsNames.ID.value] == self.id:
                logger.debug(f"{self} updated data from management: \n {user_fields}")
                if update_cache_data:
                    self.cache = user_fields
                return user_fields
        assert safe, f"User with id {self.id} was not found in organization {self.organization_name}"
        logger.debug(f"User with id {self.id} was not found in organization {self.organization_name}")
        return None

    def update_fields(self):
        raise NotImplemented("Should be implemented")

    @allure.step("Delete user")
    def _delete(self, rest_client: RestCommands, expected_status_code=200):
        """ User can't delete itself, delete from tenant """
        logger.info(f"Delete {self}")
        rest_client.users_rest.delete_user(user_name=self.get_username(), organization=self.organization_name,
                                           expected_status_code=expected_status_code)
        if expected_status_code == 200:
            self._validate_deletion()

    def __repr__(self):
        return f"User {self.id}: name '{self.get_username(from_cache=True)}' in org '{self.organization_name}'"


def get_user_fields_by_username(rest_client: RestCommands, username, organization_name, safe=False) -> dict:
    """ When creating new user the response doesn't contain any data, only status code, use this to get the
    rest data in order to initialize the user instance """
    users_fields = rest_client.users_rest.get_users(organization_name=organization_name)
    for user_fields in users_fields:
        if user_fields[UserFieldsNames.USERNAME.value] == username:
            logger.debug(f"User '{username}' updated data from management: \n {user_fields}")
            return user_fields
    assert safe, f"User {username} was not found in organization {organization_name}"
    logger.debug(f"User {username} was not found in organization {organization_name}")
    return None


def is_exists_by_username(rest_client: RestCommands, username, organization_name):
    user_fields = get_user_fields_by_username(rest_client=rest_client, username=username,
                                              organization_name=organization_name, safe=True)
    if user_fields is None:
        return False
    else:
        return True


def _compare_new_user_data(expected_data: dict, actual_data: dict):
    username = expected_data[UserFieldsNames.USERNAME.value]
    logger.info(f"Validate that user {username} created with the correct values as were passed")
    not_relevant_fields = [UserFieldsNames.PASSWORD.value, UserFieldsNames.ROLES.value]
    for field_name, expected_value in expected_data.items():
        if field_name not in not_relevant_fields:
            actual_value = actual_data[field_name]
            assert actual_value == expected_value, \
                f"User {username} not created successfully: {field_name} is {actual_value} instead of {expected_value}"
    expected_roles = expected_data[UserFieldsNames.ROLES.value]
    actual_roles = actual_data[UserFieldsNames.ROLES.value]
    assert len(expected_roles) == len(actual_roles)
    for role in expected_roles:
        assert role in actual_roles
