import time

import allure
import pytest

from infra.allure_report_handler.reporter import TEST_STEP
from tests.utils.collector_group_utils import new_group_with_collector_context


@allure.epic("Management")
@allure.feature("Inventory - collector - collector group")
@pytest.mark.inventory
@pytest.mark.collector_group_sanity
@pytest.mark.sanity
@pytest.mark.management_sanity
@pytest.mark.xray('EN-73307')
def test_delete_group_without_delete_collector(management, collector):
    """
    This test checks that after delete group (only the group without the collectors inside) that group is deleted and
    the collectors that was in the group are move to default group
    steps:
    1. create new group and move collector to this new group
    2. delete the group via ui, without deleting the collector
    3. validate the group was deleted
    4. validate that collector appears in the default group via ui
    """
    with new_group_with_collector_context(management=management, collector_agent=collector) as group_with_collector:
        target_group_name, target_collector = group_with_collector
        target_collector_name = target_collector.get_name()
        test_im_params = {
            "targetCollector": target_collector_name,
            "groupName": target_group_name
        }
        with TEST_STEP(
                f"STEP - delete the group '{target_group_name}' without deleting the collector '{target_collector_name}'"):
            management.ui_client.collectors.delete_collector_group_without_the_collectors(test_im_params)

        with TEST_STEP(f"STEP - check the group '{target_group_name}' was deleted"):
            management.ui_client.collectors.validate_the_collector_group_not_exist(test_im_params)

        with TEST_STEP(f"STEP - check the collector '{target_collector_name}' appears in the default group"):
            management.ui_client.collectors.validate_the_collector_display_under_the_default_group(test_im_params)


@allure.epic("Management")
@allure.feature("Inventory - collector - collector group")
@pytest.mark.inventory
@pytest.mark.collector_group_sanity
@pytest.mark.sanity
@pytest.mark.management_sanity
@pytest.mark.xray('EN-78549')
def test_delete_group_with_the_collector(management, collector):
    """
    This test checks that after deleting the group including the collectors within the group the collectors who were in
     the group re-register to the default group
    steps:
    1. create new group and move collector to this new group
    2. delete the group with the collectors via ui
    3. validate the group was deleted
    4. validate the collector was deleted
    5. validate that collector makes re-register and appears in the default group via ui(by waiting 60 seconds, if this
        failed maybe need to create a function for wait until collector registers)
    6. check the collector appears in the default group
    7. check the status of the collector is running in agent and rest
    """
    with new_group_with_collector_context(management=management, collector_agent=collector) as group_with_collector:
        target_group_name, target_collector = group_with_collector
        target_collector_name = target_collector.get_name()
        test_im_params = {
            "targetCollector": target_collector_name,
            "groupName": target_group_name
        }
        with TEST_STEP(
            f"STEP - delete the group '{target_group_name}' of collector '{target_collector_name}' with the collectors"):
            management.ui_client.collectors.delete_collector_group_with_the_collectors(test_im_params)

        with TEST_STEP(f"STEP - check the collector '{target_collector_name}' was deleted"):
            target_collector.wait_until_deleted()

        with TEST_STEP(f"STEP - check the group '{target_group_name}' was deleted"):
            management.ui_client.collectors.validate_the_collector_group_not_exist(test_im_params)

        with TEST_STEP(f"STEP - wait for collector '{target_collector_name}' will reregister to management"):
            time.sleep(60)

        with TEST_STEP(f"STEP - check the collector '{target_collector_name}' appears in the default group"):
            management.ui_client.collectors.validate_the_collector_display_under_the_default_group(test_im_params)

        with TEST_STEP(
                f"STEP - check the status of the collector '{target_collector_name}' is running in agent and rest"):
            collector.wait_until_agent_running()
            updated_rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
            updated_rest_collector.wait_until_running()
