from abc import abstractmethod
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.collector import CollectorFieldsNames, RestCollector
from infra.api.management_api.user import User, UserFieldsNames, LOCAL_ADMIN_ROLES
from infra.api.management_api.organization import (
    Organization, OrgFieldsNames, DEFAULT_ORGANIZATION_NAME, MANAGEMENT_REGISTRATION_PASSWORD
)
import logging
from infra.api import ADMIN_REST

logger = logging.getLogger(__name__)


class BaseApiObjFactory:
    """ Abstract base class for:
     1. Find component in management (via rest api) and return this component's rest api wrapper.
     2. Or Create new component in management (via rest api) and return this component's rest api wrapper """

    def __init__(self, factory_rest_client: RestCommands):
        self._factory_rest_client = factory_rest_client

    @abstractmethod
    def get_by_field(self, field_name, value):
        pass


class RestCollectorsFactory(BaseApiObjFactory):
    """ 1. Collectors can't be created via rest api, so find real collectors in the given organization and return
        them as rest objects.
        2. The factory's rest credentials will be set as the default auth of each of the returned
        collector objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_ip(self, ip: str, rest_client=None, safe=False) -> RestCollector:
        """ Find real collector by ip and return its rest api wrapper,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        rest_client = rest_client or self._factory_rest_client
        rest_collectors = self.get_by_field(field_name=CollectorFieldsNames.IP.value, value=ip,
                                            rest_client=rest_client, safe=safe)
        rest_collectors = [] if rest_collectors is None else rest_collectors
        if len(rest_collectors):
            assert len(rest_collectors) == 1, f"These collectors have same ip ! \n {rest_collectors}"
            return rest_collectors[0]
        if not safe:
            raise Exception(f"collectors with ip {ip} were not found in {self._organization_name}")
        logger.debug(f"collectors with ip {ip} were not found in {self._organization_name}")
        return None

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> RestCollector:
        rest_client = rest_client or self._factory_rest_client
        collectors = []
        org_name = self._organization_name
        logger.debug(f"Find collectors with field {field_name} = {value} in {org_name}")
        all_collectors = self.get_all(rest_client=rest_client, safe=safe)
        all_collectors = [] if all_collectors is None else all_collectors
        for collector in all_collectors:
            if collector.cache[field_name] == value:
                collectors.append(collector)
        logger.debug(f"Found collectors: {collectors}")
        if len(collectors):
            return collectors
        if not safe:
            raise Exception(f"collectors with field {field_name}={value} were not found in {org_name}")
        logger.debug(f"collectors with field {field_name}={value} were not found in {org_name}")
        return None

    def get_all(self, rest_client=None, safe=False):
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find all rest collectors in organization {org_name}")
        rest_collectors = []
        all_collectors_fields = rest_client.system_inventory.get_collector_info(organization=org_name)
        for collector_fields in all_collectors_fields:
            rest_collector = RestCollector(rest_client=rest_client, initial_data=collector_fields)
            rest_collectors.append(rest_collector)
        if len(rest_collectors):
            return rest_collectors
        if not safe:
            raise Exception(f"Org '{org_name}' doesn't contain collectors")
        logger.debug(f"Org '{org_name}' doesn't contain collectors")
        return None

    def create(self):
        raise NotImplemented("Collector can't be created via rest")


def get_collectors_without_org(safe=True):
    """ Return collectors that don't have organization, the returned collectors have admin credentials because
        they are under admin user (no organization) """
    logger.debug(f"Find all rest collectors that don't have organizations")
    collectors_factory = RestCollectorsFactory(organization_name=None, factory_rest_client=ADMIN_REST)
    rest_collectors = collectors_factory.get_all(safe=safe)
    return rest_collectors


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
            if not safe:
                raise Exception(f"Org '{self._organization_name}' doesn't contain user {username}")
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

    def create_local_admin(self, username, user_password, organization_name,
                           expected_status_code=200, **optional_data) -> User:
        logger.info(f"Create local admin '{username}' in organization '{organization_name}'")
        roles = LOCAL_ADMIN_ROLES
        local_admin = User.create(rest_client=self._factory_rest_client, username=username, user_password=user_password,
                                  organization_name=organization_name, roles=roles,
                                  expected_status_code=expected_status_code, **optional_data)
        return local_admin


class OrganizationsFactory(BaseApiObjFactory):
    """ Find/Create organizations and return them as rest objects.
    1. The factory's rest credentials will be set as the default auth of each of the returned
        organization objects so these credentials should be the credentials of the tenant's default local admin user
    2. Organizations factory is by use only for tenant because tenant represents organization.
    3. When searching for organizations we must add the password because
    the organizations get api doesn't return the password """

    def __init__(self, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)

    def get_by_name(self, org_name: str, registration_password: str, safe=False):
        """ Find organization by name and return its rest api wrapper with the given password """
        organizations = self.get_by_field(field_name=OrgFieldsNames.ORG_NAME.value, value=org_name,
                                          registration_password=registration_password)
        if organizations is None:
            if not safe:
                raise Exception(f"Organizations with name '{org_name}' were not found")
            logger.debug(f"Organizations with name '{org_name}' were not found")
            return None
        assert len(organizations) == 1, f"These organizations have the same name ! \n {organizations}"
        return organizations[0]

    def get_by_field(self, field_name, value, registration_password):
        """ Get organizations by field """
        organizations = []
        logger.debug(f"Find organizations with field {field_name} = {value} ")
        all_orgs_fields = ADMIN_REST.organizations.get_all_organizations()
        for org_fields in all_orgs_fields:
            if org_fields[field_name] == value:
                org = Organization(rest_client=self._factory_rest_client, password=registration_password,
                                   initial_data=org_fields)
                organizations.append(org)
        if len(organizations):
            logger.debug(f"Found these Organizations with field {field_name}={value}: \n {organizations}")
            return organizations
        return None

    def create_organization(self, organization_name, password,
                            expected_status_code=200, **optional_data) -> Organization:
        """ Create new organization with the given password and the factory's rest credentials """
        logger.info(f"Create new organization '{organization_name}'")
        organization = Organization.create(rest_client=self._factory_rest_client, name=organization_name,
                                           password=password, expected_status_code=expected_status_code,
                                           **optional_data)
        return organization


def get_default_organization():
    """ Return the default organization, the default organization has admin credentials because
        it is under admin user """
    logger.debug(f"Get the default organization: {DEFAULT_ORGANIZATION_NAME}")
    organizations_factory = OrganizationsFactory(factory_rest_client=ADMIN_REST)
    default_organization = organizations_factory.get_by_name(org_name=DEFAULT_ORGANIZATION_NAME,
                                                             registration_password=MANAGEMENT_REGISTRATION_PASSWORD)
    return default_organization
