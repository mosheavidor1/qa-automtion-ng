import logging
import time
import allure
from typing import List

from infra.api.management_api.collector_group import PolicyDefaultCollectorGroupsNames
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.api_object_factory.organizations_factory import OrganizationsFactory
from infra.api.api_object_factory.users_factory import UsersFactory
from infra.api.api_object_factory.rest_collectors_factory import RestCollectorsFactory
from infra.api.management_api.user import User
from infra.api.management_api.organization import Organization
from infra.api import ADMIN_REST
from infra.api.management_api.policy import Policy
from infra.api.management_api.collector import RestCollector
from infra.utils.policy_utils import get_default_policies
import sut_details

logger = logging.getLogger(__name__)


class TenantRestComponentsFactory:
    """ Create rest factory for each component in the tenant, with the tenant's default local admin user auth """
    def __init__(self, organization_name: str, rest_client: RestCommands):
        self._organization_name = organization_name
        self.collectors: RestCollectorsFactory = RestCollectorsFactory(organization_name=organization_name,
                                                                       factory_rest_client=rest_client)
        self.users: UsersFactory = UsersFactory(organization_name=organization_name, factory_rest_client=rest_client)


class Tenant:
    """ An ecosystem that represents only one organization with a default local admin user
        and can contain collector, users, etc """
    def __init__(self, local_admin: User, organization: Organization):
        self._organization = organization
        self._default_local_admin = local_admin
        self._rest_api_client = self._default_local_admin._rest_client
        self._rest_components = TenantRestComponentsFactory(organization_name=organization.get_name(from_cache=False),
                                                            rest_client=self._rest_api_client)

    @property
    def default_local_admin(self) -> User:
        return self._default_local_admin

    @property
    def organization(self) -> Organization:
        return self._organization

    @property
    def  rest_components(self) -> TenantRestComponentsFactory:
        """ Factory for creating/finding tenant's components like users, collectors, etc.
            With the tenant's default local admin user rest credentials """
        return self._rest_components

    @allure.step("Turn on prevention mode of this tenant")
    def turn_on_prevention_mode(self, policies: List[Policy] = None):
        policies = policies or self.get_default_policies()
        logger.info(f"Turn on prevention mode for organization {self.organization} via policies: \n {policies}")
        for policy in policies:
            policy.set_to_prevention_mode(safe=True)

    def get_default_policies(self):
        policies = get_default_policies(rest_client=self._rest_api_client,
                                        organization_name=self.organization.get_name())
        return policies

    @classmethod
    @allure.step("Create new tenant")
    def create(cls, username, user_password, organization_name, registration_password, prevention_mode=True):
        """ Create tenant from an existing/create new organization and existing/create new local admin user """
        is_new_org = False
        logger.info(f"Create tenant with organization '{organization_name}' and local admin user '{username}'")
        local_admin_rest = RestCommands(management_ip=sut_details.management_host, management_user=username,
                                        management_password=user_password, organization=organization_name)
        organizations_factory = OrganizationsFactory(factory_rest_client=local_admin_rest)
        organization = organizations_factory.get_by_name(org_name=organization_name,
                                                         registration_password=registration_password,
                                                         safe=True)
        if organization is None:
            is_new_org = True
            logger.info(f"Organization {organization_name} doesn't exist in management, create a new one")
            organization = organizations_factory.create_organization(organization_name=organization_name,
                                                                     password=registration_password)
        else:
            logger.info(f"Organization {organization_name} already exists in management")
        users_factory = UsersFactory(organization_name=organization_name, factory_rest_client=ADMIN_REST)
        default_local_admin = users_factory.get_by_username(username=username, password=user_password, safe=True)
        if default_local_admin is None:
            logger.info(f"Default Local admin {username} doesn't exist in org {organization_name}, create a new one")
            default_local_admin = users_factory.create_local_admin(username=username,
                                                                   user_password=user_password,
                                                                   organization_name=organization_name)
        else:
            logger.info(f"Default Local admin {username} already exist in org {organization_name}")

        tenant = cls(local_admin=default_local_admin, organization=organization)

        if prevention_mode and is_new_org:
            logger.info("Turn on prevention mode for the new organization")
            tenant.turn_on_prevention_mode()

        return tenant

    def delete_user(self, user: User, expected_status_code=200):
        """ Use tenant's default local admin user credentials to delete other users in this tenant """
        assert user.id != self.default_local_admin.id, \
            f"{user} is tenant's default user so can't be deleted, only when delete all the tenant"
        user._delete(rest_client=self.default_local_admin._rest_client, expected_status_code=expected_status_code)

    def require_ownership_over_collector(self, source_collector: RestCollector,
                                         target_group_name=None, safe=False) -> RestCollector:
        """ Require ownership over collector from different tenant.
            Return the updated rest collector that has the rest credentials of the current tenant """
        source_collector_ip = source_collector.get_ip()
        target_group_name = target_group_name or PolicyDefaultCollectorGroupsNames.DEFAULT_COLLECTOR_GROUP_NAME.value
        collector_org_name = source_collector.get_organization_name()
        tenant_org_name = self.organization.get_name()
        if collector_org_name == tenant_org_name:
            assert safe, f"{source_collector} already in desired organization '{tenant_org_name}'"
            logger.info(f"{source_collector} already in desired organization '{tenant_org_name}', no need to move")
            return source_collector
        logger.info(f"Move {source_collector} from org {collector_org_name} to {self} and wait few seconds")
        ADMIN_REST.system_inventory.move_collectors_to_organization(collectors_names=[source_collector.get_name()],
                                                                    target_group_name=target_group_name,
                                                                    current_collectors_organization=collector_org_name,
                                                                    target_organization=tenant_org_name)
        time.sleep(30)  # wait until collector will get the new configuration, gabi why ? see in gui the collector's organization
        logger.info(f"Validate {source_collector} moved to {self}")
        target_collector = self.rest_components.collectors.get_by_ip(ip=source_collector_ip, safe=False)
        logger.info(f"Target {target_collector} was found in {self}")
        current_group_name = target_collector.get_group_name(from_cache=True)
        assert current_group_name == target_group_name, f"{target_collector} should be in group {target_group_name}"
        return target_collector

    def __repr__(self):
        return f"Tenant with {self.organization} and {self.default_local_admin}"
