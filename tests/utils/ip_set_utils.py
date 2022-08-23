from contextlib import contextmanager
from typing import List

import allure
from infra.allure_report_handler.reporter import Reporter
from infra.api.management_api.ip_set import IpSet
from infra.multi_tenancy.tenant import Tenant
from infra.utils.utils import StringUtils
from tests.conftest import logger


@contextmanager
def new_ip_set_context(tenant: Tenant,
                       destination_event: List[str],
                       ip_set_name: str = None,
                       description: str = None,
                       exclude=None) -> IpSet:
    organization_name = tenant.organization.get_name()
    ip_set_name = ip_set_name if ip_set_name is not None else f'IP_SET_{StringUtils.generate_random_string(length=6)}'

    with allure.step(f"Setup - create ip set with the name: {ip_set_name} in organization: {organization_name}"):
        ip_set = tenant.rest_components.ip_set.create_ip_set(
            name=ip_set_name,
            organization=organization_name,
            include=destination_event,
            description=description,
            exclude=exclude)
    try:
        yield ip_set

    except Exception as original_exception:
        Reporter.report(
            f"The step inside new_ip_set context failed, going to clean all exceptions and delete the ip set,"
            f"the original exception is: {original_exception}", logger_func=logger.info)
        raise original_exception

    finally:
        with allure.step(f"Cleanup - delete IP set with the name: {ip_set_name}"):
            tenant.default_local_admin.rest_components.exceptions.delete_all(safe=True)
            ip_set.delete()
