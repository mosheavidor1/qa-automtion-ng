import logging
from contextlib import contextmanager
from typing import List

import allure

from infra.api.management_api.collector import RestCollector
from infra.api.management_api.collector_group import CollectorGroup
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.utils.utils import StringUtils

logger = logging.getLogger(__name__)


def generate_group_name() -> str:
    return f"Group_{StringUtils.generate_random_string(4)}"


@contextmanager
def new_group_with_collector_context(management: Management, collector_agent: CollectorAgent):
    """
    Context for create new collector group and move collector into it
    at the end if the new group exist will delete it
    """

    user = management.tenant.default_local_admin
    source_rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    source_group_name = source_rest_collector.get_group_name()
    new_group_name = generate_group_name()
    with allure.step(f"Setup - Create new group '{new_group_name}' and move {source_rest_collector}"):
        logger.info(f"create new group '{new_group_name}' and move {source_rest_collector} to this new group")
        user.rest_components.collector_groups.create_collector_group(group_name=new_group_name)
        source_rest_collector .move_to_different_group(target_group_name=new_group_name)
    try:
        target_rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
        yield new_group_name, target_rest_collector
    finally:
        with allure.step(
                f"Cleanup - return the collector to group {source_group_name} and delete the new group {new_group_name}"):
            updated_rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
            current_group_name = updated_rest_collector.get_group_name()
            if current_group_name != source_group_name:
                updated_rest_collector.move_to_different_group(target_group_name=source_group_name)

            if user.rest_components.collector_groups.get_by_name(name=new_group_name, safe=True) is not None:
                test_im_params = {"groupName": new_group_name}
                management.ui_client.inventory.delete_group(data=test_im_params)
            assert user.rest_components.collector_groups.get_by_name(name=new_group_name, safe=True) is None, \
                f"the new group {new_group_name} was not deleted!"


@contextmanager
def safe_create_groups_context(management: Management, rest_collector: RestCollector):
    """
    In use when we need to create several groups with/without moving collector
    """
    source_group = management.tenant.default_local_admin.rest_components.collector_groups.get_by_name(
        name=rest_collector.get_group_name())
    try:
        new_groups: List[CollectorGroup] = []
        yield new_groups
    finally:
        with allure.step(f"Cleanup - Move {rest_collector} to source group {source_group} and delete these groups {new_groups}"):
            if rest_collector.get_group_name() != source_group.name:
                rest_collector.move_to_different_group(target_group_name=source_group.name)

            assert source_group not in new_groups, f"source group {source_group} can not be deleted!"
            logger.info("Deleting each of the new temporary collector groups")
            for new_group in new_groups:
                logger.info(f"Deleting this group {new_group}")
                test_im_params = {"groupName": new_group.name}
                management.ui_client.inventory.delete_group(data=test_im_params)
