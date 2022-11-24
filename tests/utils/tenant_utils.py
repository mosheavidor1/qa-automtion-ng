import logging
from contextlib import contextmanager
from typing import Tuple, ContextManager

import allure

from infra.api import RestCommands
from infra.api.api_object_factory.organizations_factory import OrganizationsFactory
from infra.api.management_api.organization import Organization
from infra.system_components.management import Management
from infra.api.management_api.collector import RestCollector
from infra.utils.utils import StringUtils
from infra.multi_tenancy.tenant import Tenant
from infra.system_components.collector import CollectorAgent
from tests.utils.collector_group_utils import generate_group_name
from tests.utils.collector_utils import CollectorUtils, wait_till_configuration_drill_down_to_collector

logger = logging.getLogger(__name__)


@contextmanager
def new_tenant_context(management: Management,
                       collector_agent: CollectorAgent,
                       move_to_new_group=False,
                       user_name=None,
                       user_password=None,
                       org_name=None,
                       reg_password=None,
                       move_collector_to_new_org: bool = False) -> ContextManager[Tuple[Tenant, RestCollector]]:
    """ Context for creating new tenant with collector (optional) and with a new group (optional),
    at the end return the collector back to the main tenant and delete the new tenant.
    After returning collector back to main tenant and before deleting the new tenant, must wait until collector
    received back the configuration of the main tenant, otherwise it will search for a deleted tenant endless loop.
    """
    user_name = user_name or generate_username()
    user_password = user_password or generate_user_password()
    org_name = org_name or generate_org_name()
    reg_password = reg_password or generate_registration_password()

    main_tenant = management.tenant
    target_group_name = None
    target_rest_collector = None

    if move_collector_to_new_org is True and collector_agent is None:
        assert False, "Can not move collector to new organization since you did not pass collector object"

    with allure.step(f"Setup - Create new temp tenant with user {user_name}, organization {org_name}"):
        logger.info(f"Create new temp tenant with user {user_name}, organization {org_name}")

        with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
            new_tenant = management.create_temp_tenant(user_name=user_name, user_password=user_password,
                                                       organization_name=org_name, registration_password=reg_password)

        user = new_tenant.default_local_admin
        if move_to_new_group:
            target_group_name = generate_group_name()
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                user.rest_components.collector_groups.create_collector_group(group_name=target_group_name)

        if collector_agent is not None and move_collector_to_new_org is True:
            rest_collector = main_tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
            logger.info(f"Move {rest_collector} from main {main_tenant} to target {new_tenant}")
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                target_rest_collector = new_tenant.require_ownership_over_collector(source_collector=rest_collector,
                                                                                    target_group_name=target_group_name)
    try:
        yield new_tenant, target_rest_collector
    finally:
        with allure.step("Cleanup - Delete the temp tenant"):
            try:
                if target_rest_collector is not None \
                        and target_rest_collector.get_organization_name() != main_tenant.organization.get_name():
                    logger.info(f"Return back the {target_rest_collector} to the main tenant {main_tenant}")
                    with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                        main_tenant.require_ownership_over_collector(source_collector=target_rest_collector)
                    logger.info(f"Wait until {collector_agent} will get the configuration from {main_tenant}")
                    CollectorUtils.wait_for_registration_password(collector_agent=collector_agent,
                                                                  tenant=main_tenant, start_collector=True)
            finally:
                logger.info(f"Validate that temp tenant {new_tenant} has no collectors and delete it")
                remaining_rest_collectors = new_tenant.rest_components.collectors.get_all(safe=True)
                assert remaining_rest_collectors is None, f"Temp {new_tenant} still has " \
                                                          f"collectors: {remaining_rest_collectors}"
                with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                    management.delete_tenant(temp_tenant=new_tenant)


def generate_username():
    return f"User_{StringUtils.generate_random_string()}"


def generate_user_password():
    return f"User_Pass1{StringUtils.generate_random_string(length=5)}"


def generate_org_name():
    return f"Organization_{StringUtils.generate_random_string()}"


def generate_registration_password():
    return f"RegPass{StringUtils.generate_random_string()}"


@contextmanager
def new_organization_without_user_context(management: Management,
                                          organization_name=None,
                                          registration_password=None,
                                          collector_agent: CollectorAgent = None) -> Organization:
    """
    Context for creating new organization without user, at the end delete the new organization.
    """
    user_name = generate_username()
    user_password = generate_user_password()
    organization_name = organization_name or generate_org_name()
    registration_password = registration_password or generate_registration_password()

    with allure.step("Setup - Create a new organization without user"):
        local_admin_rest = RestCommands(management_ip=management.host_ip,
                                        rest_api_user_name=user_name,
                                        rest_api_user_password=user_password,
                                        organization=organization_name)
        organizations_factory = OrganizationsFactory(factory_rest_client=local_admin_rest)
        organization = organizations_factory.get_by_name(org_name=organization_name,
                                                         registration_password=registration_password,
                                                         safe=True)
        assert organization is None, f"Bug in infra! generate a new organization name {organization_name} that already exists"
        logger.info(f"Organization {organization_name} doesn't exist in management, create a new one")
        with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
            new_organization = organizations_factory.create_organization(organization_name=organization_name,
                                                                         password=registration_password)
    try:
        yield new_organization
    finally:
        with allure.step(f"Cleanup - Delete the new organization {new_organization}"):
            assert new_organization.get_name() != management.tenant.organization.get_name(), \
                f"default organization can not be deleted!"
            logger.info(f"Delete the new organization {new_organization}")
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                new_organization._delete()

