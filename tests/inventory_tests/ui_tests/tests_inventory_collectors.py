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
        with TEST_STEP(f"STEP - delete the group '{target_group_name}' without deleting the collector '{target_collector_name}'"):
            management.ui_client.collectors.delete_collector_group_without_the_collectors(test_im_params)

        with TEST_STEP(f"STEP - check the group '{target_group_name}' was deleted"):
            management.ui_client.collectors.validate_the_collector_group_not_exist(test_im_params)

        with TEST_STEP(f"STEP - check the collector '{target_collector_name}' appears in the default group"):
            management.ui_client.collectors.validate_the_collector_display_under_the_default_group(test_im_params)
