import logging
import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.api.management_api.policy import DefaultPoliciesNames
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.collector_group_utils import safe_create_groups_context, generate_group_name
from tests.utils.collector_utils import isolate_collector_context, is_config_file_is_partial


logger = logging.getLogger(__name__)


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.sanity
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
@pytest.mark.xray('EN-76225')
def test_receive_partial_configuration_after_remove_collector_from_isolation_in_windows_os(management, collector):
    """
    This test is validated that after remove collector from isolation mode,
    a new config file received, and it is a partial configuration.
    1. Isolate collector and Fetch the latest config file, before removing isolation
    2. Remove collector from isolation mode
    3. Validate the collector received partial configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"
    tenant = management.tenant

    with isolate_collector_context(tenant=tenant, collector_agent=collector):
        with TEST_STEP(f"STEP - Isolate collector and Fetch the latest config ,before removing isolation"):
            Reporter.report("Fetch config files before remove from isolation, in order to validate later the diff \
                            after remove from isolation", INFO)
            current_latest_config_file = collector.get_the_latest_config_file_details()

    with TEST_STEP("STEP - Validate collector received a new partial config file that related to the remove isolation action"):
        collector.wait_for_new_config_file(latest_config_file_details=current_latest_config_file)
        latest_config_file_details_after_remove_isolation = collector.get_the_latest_config_file_details()
        assert is_config_file_is_partial(config_file_details=latest_config_file_details_after_remove_isolation), \
            f"Config file after remove isolation collector is not partial, these are the details \n {latest_config_file_details_after_remove_isolation}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.sanity
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
@pytest.mark.xray('EN-76204')
def test_receive_partial_configuration_after_assign_collector_to_empty_group_that_assigned_to_execution_prevention_policy_in_windows_os(management, collector):
    """
    This test is validated that after moving collector to an empty group that assigned to policy
    Execution Prevention, a new config file received, and it is a partial configuration.
    STEPS:
    1. Create new group, without assigned policies, and move there the collector,
       because in this test we need the policy assigned groups to be empty without collectors and because by default,
       the default collector group has a collector, and it is assigned to policy therefore we need to move the collector
       to a new group that is unassigned to policy.
    2. Create a new empty collector group and assign to policy Execution Prevention
    3. Fetch the latest config file before moving collector
    4. Move the collector to the new group that assigned to policy Execution Prevention
    5. Validate that collector received a partial config after moving collector to the assigned new empty group
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"
    organization_rest_collectors = management.tenant.rest_components.collectors.get_all(safe=True)
    assert len(organization_rest_collectors) == 1, f"This test supported only in one collector per organization"
    tenant = management.tenant
    user = tenant.default_local_admin
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    policy = user.rest_components.policies.get_by_name(policy_name=DefaultPoliciesNames.EXECUTION_PREVENTION.value)

    with safe_create_groups_context(management=management, rest_collector=rest_collector) as new_groups:
        with TEST_STEP(f"Setup - Create new group, without assigned policies, and move there {rest_collector}"):
            new_temp_group = user.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())
            rest_collector.move_to_different_group(target_group_name=new_temp_group.name)
            new_groups.append(new_temp_group)

        with TEST_STEP(f"STEP - Create a new empty collector group and assign to {policy}"):
            new_group = user.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())
            new_groups.append(new_group)
            policy.assign_to_collector_group(group_name=new_group.name)

        with TEST_STEP(f"STEP - Fetch the latest config before moving {rest_collector}"):
            latest_config_file_before_moving_collector = collector_agent.get_the_latest_config_file_details()

        with TEST_STEP(f"STEP - Move {rest_collector} to the assigned group {new_group.name}"):
            rest_collector.move_to_different_group(target_group_name=new_group.name)

        with TEST_STEP("STEP - Validate collector received a new partial config file that related to the last action"):
            collector.wait_for_new_config_file(latest_config_file_details=latest_config_file_before_moving_collector)
            latest_config_file_after_moving_collector = collector.get_the_latest_config_file_details()
            assert is_config_file_is_partial(config_file_details=latest_config_file_after_moving_collector), \
                f"Config file after move collector to {new_group} that is assigned to {policy} is not partial, \
                these are the details {latest_config_file_after_moving_collector}"
