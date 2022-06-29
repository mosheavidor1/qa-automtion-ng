import logging
from contextlib import contextmanager
from typing import Tuple, ContextManager
from infra.system_components.management import Management
from infra.api.management_api.collector import RestCollector
from infra.utils.utils import StringUtils
from infra.multi_tenancy.tenant import Tenant
from infra.system_components.collector import CollectorAgent
from tests.utils.collector_utils import CollectorUtils

logger = logging.getLogger(__name__)


@contextmanager
def new_tenant_context(management: Management, collector_agent: CollectorAgent, user_name=None, user_password=None,
                       org_name=None, reg_password=None) -> ContextManager[Tuple[Tenant, RestCollector]]:
    """ Context for creating new tenant with collector, at the end return the collector back to the main tenant
    and delete the new tenant.
    After returning collector back to main tenant and before deleting the new tenant, must to wait until collector
    received back the configuration of the main tenant, otherwise it will search for a deleted tenant endless loop.
    """
    user_name = user_name or generate_username()
    user_password = user_password or generate_user_password()
    org_name = org_name or generate_org_name()
    reg_password = reg_password or generate_registration_password()

    main_tenant = management.tenant
    rest_collector = main_tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    logger.info(f"Create new temp tenant with user {user_name}, organization {org_name}, {rest_collector}")
    new_tenant = management.create_temp_tenant(user_name=user_name, user_password=user_password,
                                               organization_name=org_name, registration_password=reg_password)
    logger.info(f"Move {rest_collector} from main {main_tenant} to target {new_tenant}")
    target_rest_collector = new_tenant.require_ownership_over_collector(source_collector=rest_collector)
    try:
        yield new_tenant, target_rest_collector
    finally:
        logger.info(f"Return back the {target_rest_collector} to the main tenant {main_tenant}")
        main_tenant.require_ownership_over_collector(source_collector=target_rest_collector)
        logger.info(f"Wait until {collector_agent} will get the configuration from {main_tenant}")
        CollectorUtils.wait_for_configuration(collector_agent=collector_agent, tenant=main_tenant,
                                              start_collector=True)
        logger.info(f"Validate that temp tenant {new_tenant} has no collectors and delete it")
        remaining_rest_collectors = new_tenant.rest_components.collectors.get_all(safe=True)
        assert remaining_rest_collectors is None, f"Temp {new_tenant} still has collectors: {remaining_rest_collectors}"
        management.delete_tenant(temp_tenant=new_tenant)


def generate_username():
    return f"User_{StringUtils.generate_random_string()}"


def generate_user_password():
    return f"UserPass{StringUtils.generate_random_string()}"


def generate_org_name():
    return f"Organization_{StringUtils.generate_random_string()}"


def generate_registration_password():
    return f"RegPass{StringUtils.generate_random_string()}"
