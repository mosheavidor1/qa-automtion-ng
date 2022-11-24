import logging
import allure
import pytest

from infra.utils.utils import StringUtils
from tests.utils.collector_group_utils import generate_group_name
from tests.utils.collector_utils import is_config_file_received_in_collector, \
    wait_till_configuration_drill_down_to_collector, CollectorUtils
from tests.utils.environment_utils import add_collectors_from_pool
from tests.utils.tenant_utils import new_tenant_context, new_organization_without_user_context
from infra.allure_report_handler.reporter import TEST_STEP
from infra.enums import FortiEdrSystemState, CollectorConfigurationTypes, CollectorTypes
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.aggregator_utils import revive_aggregator_on_failure_context
from tests.utils.management_utils import ManagementUtils, revive_management_on_failure_context

logger = logging.getLogger(__name__)


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-76208')
def test_receive_full_configuration_after_delete_organization_in_windows_os(management, collector):
    """
    This test is validated that after delete an organization ,a new config file received and it is a full configuration.
    1. Create a new organization and Fetch the latest config ,before delete organization
    2. Delete the new organization
    3. Validate the collector received full configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tmp_tenant = None
    rnd = StringUtils.generate_random_string(length=3)
    user_name = f'tmp_user_{rnd}'
    org_name = f'organization_{rnd}'
    with wait_till_configuration_drill_down_to_collector(collector_agent=collector):
        tmp_tenant = management.create_temp_tenant(user_name=user_name,
                                                   user_password="User_Pass123456",
                                                   organization_name=org_name,
                                                   registration_password='12345678')

    collector_datetime_before_delete_org = collector.get_current_datetime()

    with wait_till_configuration_drill_down_to_collector(collector_agent=collector):
        management.delete_tenant(temp_tenant=tmp_tenant)

    with TEST_STEP("STEP - Validate collector received a new full config file that related to the delete org action"):
        latest_config_file_details_after_delete_org = collector.get_the_latest_config_update_file_details()
        assert is_config_file_received_in_collector(collector=collector,
                                                    config_file_details=latest_config_file_details_after_delete_org,
                                                    first_log_date_time=collector_datetime_before_delete_org,
                                                    desired_config_type=CollectorConfigurationTypes.FULL.value), \
            f"Config file after deleting org '{tmp_tenant.organization}' is not full, these are the details \
            {latest_config_file_details_after_delete_org}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-76209')
def test_receive_full_configuration_after_create_organization_in_windows_os(management, collector):
    """
    This test is validated that after create an organization ,a new config file received and it is a full configuration.
    1. Fetch the latest config before creating an organization
    2. Create a new organization
    3. Validate the collector received full configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    with TEST_STEP(f"STEP - Fetch the latest config before creating a new organization"):
        collector_datetime_before_create_org = collector.get_current_datetime()

    with new_organization_without_user_context(management=management, collector_agent=collector) as new_org:
        with TEST_STEP("STEP - Validate collector received a new full config file that related to the create org action"):
            latest_config_file_details_after_create_org = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_details_after_create_org,
                                                        first_log_date_time=collector_datetime_before_create_org,
                                                        desired_config_type=CollectorConfigurationTypes.FULL.value),\
                f"Config file after creating {new_org} is not full, these are the details\
                {latest_config_file_details_after_create_org}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-76206')
def test_receive_full_configuration_after_restart_management_in_windows_os(management, collector):
    """
    1. Restart management and Fetch the latest config file before restart management
    2. Validate the collector received full configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    with revive_management_on_failure_context(management=management):
        with TEST_STEP("STEP - Restart management and Fetch the latest config file before restart management"):
            collector_datetime_before_restart_mng = collector.get_current_datetime()

            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                logger.info(f"restart management {management}")
                management.restart_service()

                with TEST_STEP("STEP - Validate service is up and the collector is running"):
                    ManagementUtils.wait_till_operational(management=management)
                    collector_agent.wait_until_agent_running()
                    rest_collector.wait_until_running()

        with TEST_STEP("STEP - Validate collector received a new full config file that related to the restart action"):
            latest_config_file_details_after_restart_mng = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_details_after_restart_mng,
                                                        first_log_date_time=collector_datetime_before_restart_mng,
                                                        desired_config_type=CollectorConfigurationTypes.FULL.value), \
                f"Config file after restart management is not full, these are the details: \
                {latest_config_file_details_after_restart_mng}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-76207')
def test_receive_full_configuration_after_restart_aggregator_in_windows_os(management, aggregator, collector):
    """
    1. Restart aggregator and Fetch the latest config file before restart aggregator
    2. Validate the collector received full configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    with revive_aggregator_on_failure_context(aggregator=aggregator):
        with TEST_STEP("STEP - Restart aggregator and Fetch the latest config file before restart aggregator"):
            collector_datetime_before_restart_agg = collector.get_current_datetime()

            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                logger.info(f"restart aggregator {aggregator}")
                aggregator.restart_service()

                with TEST_STEP("STEP - Validate aggregator service is up and the collector is running"):
                    aggregator.wait_until_service_will_be_in_desired_state(desired_state=FortiEdrSystemState.RUNNING)
                    collector_agent.wait_until_agent_running()
                    rest_collector.wait_until_running()

        with TEST_STEP("STEP - Validate collector received a new full config file that related to the restart action"):
            latest_config_file_details_after_restart_agg = collector.get_the_latest_config_update_file_details()
            assert is_config_file_received_in_collector(collector=collector,
                                                        config_file_details=latest_config_file_details_after_restart_agg,
                                                        first_log_date_time=collector_datetime_before_restart_agg,
                                                        desired_config_type=CollectorConfigurationTypes.FULL.value), \
                f"Config file after restart aggregator is not full, these are the details: \
                {latest_config_file_details_after_restart_agg}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-79583')
def test_receive_full_configuration_after_move_collector_to_non_empty_group_in_different_organization_in_windows_os(management, aggregator, collector):
    """
      This test is validated that after moving collector to a new group with collector in a different organization
      a new config file received, and it is a full configuration.
      1. Create a new organization and a new collector group with collector from collectors pool
      2. Fetch the latest config file before moving collector
      3. Move the collector to the new group with collector in the new organization
      4. Validate that collector received a full config after moving collector to different organization
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tenant = management.tenant
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    desired_version = rest_collector.get_version()
    desired_collectors = {
        CollectorTypes.WINDOWS_10_64: 1
    }

    with new_tenant_context(management=management,
                            move_collector_to_new_org=False,
                            collector_agent=collector_agent) as new_tenant_and_collector:
        new_tenant, target_rest_collector = new_tenant_and_collector
        with TEST_STEP(f"Create new group in new {new_tenant} with collector from collectors pool"):
            with add_collectors_from_pool(management=management,
                                          tenant=new_tenant,
                                          desired_version=desired_version,
                                          aggregator_ip=aggregator.host_ip,
                                          organization=new_tenant.organization.get_name(),
                                          registration_password=new_tenant.organization.registration_password,
                                          desired_collectors_dict=desired_collectors) as dynamic_collectors:
                additional_collector_agent = dynamic_collectors[0]
                additional_rest_collector = new_tenant.rest_components.collectors.get_by_ip(ip=additional_collector_agent.host_ip)
                logger.info(f"create a new group and move there the additional {additional_collector_agent}")

                new_group = new_tenant.default_local_admin.rest_components.collector_groups.create_collector_group(
                    group_name=generate_group_name())

                with wait_till_configuration_drill_down_to_collector(collector_agent=additional_collector_agent):
                    additional_rest_collector.move_to_different_group(target_group_name=new_group.name)

                with TEST_STEP(f"STEP - Fetch the latest config file before moving {collector_agent} to new {new_group}"):
                    collector_datetime_before_moving_collector = collector.get_current_datetime()
                try:
                    with TEST_STEP(f"STEP - Move {rest_collector} to the new {new_group} in new {new_tenant}"):
                        with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                            rest_collector = new_tenant.require_ownership_over_collector(source_collector=rest_collector,
                                                                                         target_group_name=new_group.name)
                    with TEST_STEP("STEP - Validate collector received a new full config file that related to the last action"):
                        latest_config_file_after_moving_collector = collector.get_the_latest_config_update_file_details()
                        assert is_config_file_received_in_collector(collector=collector,
                                                                    config_file_details=latest_config_file_after_moving_collector,
                                                                    first_log_date_time=collector_datetime_before_moving_collector,
                                                                    desired_config_type=CollectorConfigurationTypes.FULL.value), \
                            f"Config file after move {rest_collector} to the new group with collector \
                            is not full, these are the details {latest_config_file_after_moving_collector}"

                finally:
                    logger.info(f"Cleanup - return {rest_collector} from {new_tenant} back to {tenant}")
                    with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                        tenant.require_ownership_over_collector(source_collector=rest_collector)
                    with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                        CollectorUtils.wait_for_registration_password(collector_agent=collector_agent, tenant=tenant)


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.configuration_windows_collector
@pytest.mark.configuration_windows_collector_sanity
@pytest.mark.xray('EN-79306')
def test_receive_full_configuration_after_move_collector_to_empty_group_in_different_organization_in_windows_os(management, collector):
    """
      This test is validated that after moving collector to an empty group in a different organization a new config file
      received, and it is a full configuration.
      1. Create a new organization with a new collector group and fetch the latest config file before moving collector
      2. Move the collector to the new group in the new organization
      3. Validate that collector received a full config after moving collector to different organization
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    tenant = management.tenant
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)

    with new_tenant_context(management=management,
                            collector_agent=collector_agent,
                            move_collector_to_new_org=False) as new_tenant_and_collector:
        new_tenant, target_rest_collector = new_tenant_and_collector
        # with TEST_STEP(f"STEP - Create a new group and Fetch the latest config file before moving {collector_agent} to this group"):
            # here we don't need to wait since collector should not get configuration
            # collector gets an update only when new organization is create\removed and if some change was happend in his org
            # in this step, the organization is on his original tenant, so operation in the new tenants
            # should not be sent to the collector that found on different (original org)
            # new_group = new_tenant.default_local_admin.rest_components.collector_groups.create_collector_group(group_name=generate_group_name())
            # time.sleep(120)
        try:
            # with TEST_STEP(f"STEP - Move {rest_collector} to the new group {new_group} in new tenant {new_tenant}"):
            with TEST_STEP(f"STEP - Move {rest_collector} to the Default group (empty at the moment) in new tenant {new_tenant}"):
                collector_datetime_before_moving_collector = collector.get_current_datetime()
                with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                    rest_collector = new_tenant.require_ownership_over_collector(source_collector=rest_collector,
                                                                                 target_group_name=None)

            with TEST_STEP("STEP - Validate collector received a new full config file that related to the last action"):
                latest_config_file_details_after_moving_collector = collector.get_the_latest_config_update_file_details()
                assert is_config_file_received_in_collector(collector=collector,
                                                            config_file_details=latest_config_file_details_after_moving_collector,
                                                            first_log_date_time=collector_datetime_before_moving_collector,
                                                            desired_config_type=CollectorConfigurationTypes.FULL.value), \
                    f"Config file after move {rest_collector} to new group in new organization \
                            is not full, these are the details {latest_config_file_details_after_moving_collector}"

        finally:
            logger.info(f"Cleanup - return {rest_collector} from {new_tenant} back to {tenant}")
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                tenant.require_ownership_over_collector(source_collector=rest_collector)
            CollectorUtils.wait_for_registration_password(collector_agent=collector_agent, tenant=tenant)

