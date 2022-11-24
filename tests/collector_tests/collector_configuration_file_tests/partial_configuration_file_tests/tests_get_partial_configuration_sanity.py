import logging

import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.api.management_api.security_policy import DefaultPoliciesNames
from infra.enums import CollectorConfigurationTypes, CollectorTypes
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.collector_group_utils import return_collector_to_original_groups_context, generate_group_name, \
    new_group_with_collector_context
from tests.utils.collector_utils import isolate_collector_context, is_config_file_received_in_collector, CollectorUtils, \
    wait_till_configuration_drill_down_to_collector
from tests.utils.environment_utils import add_collectors_from_pool
from tests.utils.tenant_utils import new_tenant_context

logger = logging.getLogger(__name__)


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
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
            collector_datetime_before_remove_isolation = collector.get_current_datetime()

    with TEST_STEP("STEP - Validate collector received a new partial config file that related to the remove isolation action"):
        latest_config_file_details_after_remove_isolation = collector.get_the_latest_config_update_file_details()
        assert is_config_file_received_in_collector(collector=collector,
                                                    config_file_details=latest_config_file_details_after_remove_isolation,
                                                    first_log_date_time=collector_datetime_before_remove_isolation,
                                                    desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
            f"Config file after remove isolation collector is not partial, these are the details \
            {latest_config_file_details_after_remove_isolation}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
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
    policy = user.rest_components.security_policies.get_by_name(policy_name=DefaultPoliciesNames.EXECUTION_PREVENTION.value)

    with return_collector_to_original_groups_context(management=management,
                                                     rest_collector=rest_collector,
                                                     collector_agent=collector_agent) as new_groups:
        with TEST_STEP(f"Setup - Create new group, without assigned policies, and move there {rest_collector}"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                new_temp_group = user.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())

            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                    rest_collector.move_to_different_group(target_group_name=new_temp_group.name)

            new_groups.append(new_temp_group)

        with TEST_STEP(f"STEP - Create a new empty collector group and assign to {policy}"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                new_group = user.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())
            new_groups.append(new_group)

            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                policy.assign_to_collector_group(group_name=new_group.name)

        with TEST_STEP(f"STEP - Fetch the latest config before moving {rest_collector}"):
            collector_datetime_before_moving_collector = collector.get_current_datetime()

        with TEST_STEP(f"STEP - Move {rest_collector} to the assigned group {new_group.name}"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                rest_collector.move_to_different_group(target_group_name=new_group.name)

        with TEST_STEP("STEP - Validate collector received a new partial config file that related to the last action"):
            latest_config_file_after_moving_collector = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_after_moving_collector,
                                                        first_log_date_time=collector_datetime_before_moving_collector,
                                                        desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
                f"Config file after move collector to {new_group} that is assigned to {policy} is not partial, \
                these are the details {latest_config_file_after_moving_collector}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-79302')
def test_receive_partial_configuration_after_move_collector_to_empty_group_in_same_organization_in_windows_os(management, collector):
    """
      This test is validated that after moving collector to an empty group in the same organization a new config file
      received, and it is a partial configuration
      1. Create a new group and fetch the latest config file before moving collector
      2. Move the collector to the new group in the same organization
      3. Validate that collector received a partial config after moving collector in same organization
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tenant = management.tenant
    user = tenant.default_local_admin
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)

    with return_collector_to_original_groups_context(management=management,
                                                     rest_collector=rest_collector,
                                                     collector_agent=collector_agent) as new_groups:
        with TEST_STEP(f"STEP - Create a new group and fetch the latest config file before moving {rest_collector}"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                new_group = user.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())

            new_groups.append(new_group)
            collector_datetime_before_moving_collector = collector.get_current_datetime()

        with TEST_STEP(f"STEP - Move {rest_collector} to the new group {new_group.name} in the same organization"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                rest_collector.move_to_different_group(target_group_name=new_group.name)

        with TEST_STEP("STEP - Validate collector received a new partial config file that related to the last action"):
            latest_config_file_details_after_moving_collector = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_details_after_moving_collector,
                                                        first_log_date_time=collector_datetime_before_moving_collector,
                                                        desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
                   f"Config file after move {rest_collector} to {new_group} is not partial, \
                   these are the details {latest_config_file_details_after_moving_collector}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-76219')
def test_receive_partial_configuration_after_move_collector_from_group_with_collector_to_group_with_collector(management, aggregator, collector):
    """
     This test is validated that after moving collector from group with collector to a new group with collector
     a new config file received, and it is a partial configuration.
     1. Add a collector from collectors pool to default collector group
     2. Create new group with collector from collectors pool
     3. Fetch the latest config file before moving collector
     4. Move the collector to the new group with collector
     5. Validate that collector received a partial config after moving collector
    """
    collector_agent = collector
    tenant = management.tenant
    user = tenant.default_local_admin
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    desired_version = rest_collector.get_version()
    desired_collectors = {
        CollectorTypes.WINDOWS_10_64: 2
    }

    logger.info("Create 2 collectors from collectors pool")
    with add_collectors_from_pool(management=management,
                                  tenant=tenant,
                                  desired_version=desired_version,
                                  aggregator_ip=aggregator.host_ip,
                                  organization=tenant.organization.get_name(),
                                  registration_password=tenant.organization.registration_password,
                                  desired_collectors_dict=desired_collectors) as dynamic_collectors:
        additional_collector_agent = dynamic_collectors[0]
        with TEST_STEP(f"Create new group with {additional_collector_agent} from collectors pool"):
            logger.info(f"create a new group and move there the additional {additional_collector_agent}")
            with new_group_with_collector_context(management=management, collector_agent=additional_collector_agent) as group_with_collector:
                new_group_name, target_rest_collector = group_with_collector

                with TEST_STEP(f"STEP - Fetch the latest config before moving {rest_collector}"):
                    collector_datetime_before_moving_collector = collector.get_current_datetime()

                with TEST_STEP(f"STEP - Move {rest_collector} to the new group '{new_group_name}' with {target_rest_collector}"):
                    logger.info(f"Move {rest_collector} to the new group '{new_group_name}' with {target_rest_collector}")
                    with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                        rest_collector.move_to_different_group(target_group_name=new_group_name)

                with TEST_STEP("STEP - Validate that collector received a partial config after moving collector"):
                    latest_config_file_details_after_moving_collector = collector.get_the_latest_config_update_file_details()
                    assert is_config_file_received_in_collector(collector=collector,
                                                                config_file_details=latest_config_file_details_after_moving_collector,
                                                                first_log_date_time=collector_datetime_before_moving_collector,
                                                                desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
                        f"Config file after move {rest_collector} to new group '{new_group_name}' with {target_rest_collector} \
                        is not partial, these are the details {latest_config_file_details_after_moving_collector}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-79582')
def test_receive_partial_configuration_after_move_collector_to_non_empty_group_in_same_organization_in_windows_os(management, aggregator, collector):
    """
     This test is validated that after moving collector to a new group with collector in the same organization
      a new config file received, and it is a partial configuration.
      1. Create a new collector group with collector from collectors pool
      2. Fetch the latest config file before moving collector
      3. Move the collector to the new group with collector in the same organization
      4. Validate that collector received a partial config after moving collector to same organization
    """
    collector_agent = collector
    tenant = management.tenant
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    desired_version = rest_collector.get_version()
    desired_collectors = {
        CollectorTypes.WINDOWS_10_64: 1
    }

    with TEST_STEP("Create new group with collector from collectors pool"):
        with add_collectors_from_pool(management=management,
                                      tenant=tenant,
                                      desired_version=desired_version,
                                      aggregator_ip=aggregator.host_ip,
                                      organization=tenant.organization.get_name(),
                                      registration_password=tenant.organization.registration_password,
                                      desired_collectors_dict=desired_collectors) as dynamic_collectors:
            additional_collector_agent = dynamic_collectors[0]

            logger.info(f"create a new group and move there the additional {additional_collector_agent}")
            with new_group_with_collector_context(management=management,
                                                  collector_agent=additional_collector_agent) as group_with_collector:
                new_group_name, target_rest_collector = group_with_collector

                with TEST_STEP(f"STEP - Fetch the latest config before moving {rest_collector}"):
                    collector_datetime_before_moving_collector = collector.get_current_datetime()

                with return_collector_to_original_groups_context(management=management,
                                                                 rest_collector=rest_collector,
                                                                 collector_agent=collector_agent) as new_groups:

                    with TEST_STEP(f"STEP - Move {rest_collector} to the new group '{new_group_name}' with {target_rest_collector}"):
                        logger.info(f"Move {rest_collector} to the new group '{new_group_name}' with {target_rest_collector}")
                        with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                            # collector_group_obj = management.tenant.default_local_admin.rest_components.collector_groups.get_by_name(name=new_group_name)
                            rest_collector.move_to_different_group(target_group_name=new_group_name)
                            # new_groups.append(collector_group_obj)

                    with TEST_STEP("STEP - Validate that collector received a partial config after moving collector"):
                        latest_config_file_after_moving_collector = collector.get_the_latest_config_update_file_details()

                        assert is_config_file_received_in_collector(collector=collector,
                                                                    config_file_details=latest_config_file_after_moving_collector,
                                                                    first_log_date_time=collector_datetime_before_moving_collector,
                                                                    desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
                            f"Config file after move {rest_collector} to new group '{new_group_name}' with {target_rest_collector} \
                            is not partial, these are the details {latest_config_file_after_moving_collector}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-78369')
def test_receive_partial_configuration_after_assign_collector_group_to_security_policy_in_windows_os(management, collector):
    """
    This test is validated that after assigned group with collector to security policy Execution Prevention,
    a new config file received, and it is a partial configuration.
    1. Create a new group that unassigned to policy Execution Prevention and move a collector to this group
    2. Fetch the latest config file before assign new group to policy Execution Prevention
    3. Assign the new collector group to policy Execution Prevention
    4. Validate that collector received a partial config after assign new group to policy Execution Prevention
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tenant = management.tenant
    user = tenant.default_local_admin
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    policy = user.rest_components.security_policies.get_by_name(policy_name='Execution Prevention')

    with new_group_with_collector_context(management=management, collector_agent=collector_agent) as group_with_collector:
        new_group_name, target_rest_collector = group_with_collector

        with TEST_STEP(f"STEP - Fetch the latest config file before assign group '{new_group_name}' to {policy}"):
            collector_datetime_before_assign_group = collector.get_current_datetime()

        with TEST_STEP(f"STEP - Assign the new collector group '{new_group_name}' to {policy}"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                policy.assign_to_collector_group(group_name=new_group_name)

        with TEST_STEP("STEP - Validate collector received a new partial config file that related to the last action"):
            latest_config_file_after_assign_group = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_after_assign_group,
                                                        first_log_date_time=collector_datetime_before_assign_group,
                                                        desired_config_type=CollectorConfigurationTypes.PARTIAL.value), \
                f"Config file after move {rest_collector} to the new group with collector \
                is not partial, these are the details {latest_config_file_after_assign_group}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector partial configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-79581')
def test_receive_partial_configuration_after_assign_collector_to_non_empty_security_policy_in_windows_os(management, aggregator, collector):
    """
    This test is validated that after moving collector to a group with collector, that assigned to
    policy Execution Prevention, a new config file received, and it is a partial configuration.
    STEPS:
    1. Create a new collector from collectors pool, in default collector group that assigned by default to
       policy Execution Prevention
    2. Create new group, without assigned policies, and move there a collector from default collector group, in order
       that this collector will not be assigned to policy
    3. Fetch the latest config file before moving collector
    4. Move the collector from new group to the default collector group that assigned by default to policy Execution
       Prevention and has a collector
    5. Validate that collector received a partial config after moving collector to the assigned group with collector
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tenant = management.tenant
    user = tenant.default_local_admin
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    policy = user.rest_components.security_policies.get_by_name(policy_name=DefaultPoliciesNames.EXECUTION_PREVENTION.value)
    desired_version = rest_collector.get_version()
    desired_collectors = {
        CollectorTypes.WINDOWS_10_64: 1
    }

    Reporter.report("STEP - Create a new collector from collectors pool, in default collector group that assigned by \
    default to policy Execution Prevention")
    with add_collectors_from_pool(management=management,
                                  tenant=tenant,
                                  desired_version=desired_version,
                                  aggregator_ip=aggregator.host_ip,
                                  organization=tenant.organization.get_name(),
                                  registration_password=tenant.organization.registration_password,
                                  desired_collectors_dict=desired_collectors) as dynamic_collectors:
        additional_collector_agent = dynamic_collectors[0]
        additional_rest_collector = tenant.rest_components.collectors.get_by_ip(
            ip=additional_collector_agent.host_ip)

        Reporter.report("STEP - Create new group, without assigned policies, and move there a collector from default "
                        "collector group")
        with new_group_with_collector_context(management=management, collector_agent=collector_agent):

            with TEST_STEP(f"STEP - Fetch the latest config before moving {rest_collector}"):
                collector_datetime_before_moving_collector = collector.get_current_datetime()

            with TEST_STEP(f"STEP - Move {rest_collector} to the assigned group with {additional_rest_collector}"):
                with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                    rest_collector.move_to_different_group(target_group_name=additional_rest_collector.get_group_name())

            with TEST_STEP("STEP - Validate collector received a new partial config file that related to the last action"):
                latest_config_file_after_moving_collector = collector.get_the_latest_config_update_file_details()
                assert is_config_file_received_in_collector(collector=collector,
                                                            config_file_details=latest_config_file_after_moving_collector,
                                                            first_log_date_time=collector_datetime_before_moving_collector,
                                                            desired_config_type=CollectorConfigurationTypes.PARTIAL.value),\
                    f"Config file after move collector to default collector group with collector, that is assigned to \
                    {policy} is not partial, these are the details {latest_config_file_after_moving_collector}"
