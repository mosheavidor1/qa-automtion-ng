import logging
import allure
import pytest
from tests.utils.tenant_utils import new_tenant_context, new_organization_without_user_context
from infra.allure_report_handler.reporter import TEST_STEP
from infra.enums import FortiEdrSystemState
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.aggregator_utils import revive_aggregator_on_failure_context
from tests.utils.collector_utils import is_config_file_is_partial
from tests.utils.management_utils import ManagementUtils, revive_management_on_failure_context

logger = logging.getLogger(__name__)


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.sanity
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
@pytest.mark.xray('EN-76208')
def test_receive_full_configuration_after_delete_organization_in_windows_os(management, collector):
    """
    This test is validated that after delete an organization ,a new config file received and it is a full configuration.
    1. Create a new organization and Fetch the latest config ,before delete organization
    2. Delete the new organization
    3. Validate the collector received full configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    with new_tenant_context(management=management) as new_tenant:
        new_tenant, target_collector = new_tenant
        new_org_name = new_tenant.organization.get_name()
        with TEST_STEP(f"STEP - Fetch the latest config before deleting the new organization {new_org_name}"):
            latest_config_file_details_before_delete_org = collector.get_the_latest_config_file_details()

    with TEST_STEP("STEP - Validate collector received a new full config file that related to the delete organization action"):
        collector.wait_for_new_config_file(latest_config_file_details=latest_config_file_details_before_delete_org)
        latest_config_file_details_after_delete_org = collector.get_the_latest_config_file_details()
        assert not is_config_file_is_partial(config_file_details=latest_config_file_details_after_delete_org), \
            f"Config file after deleting org '{new_org_name}' is not full, these are the details \n {latest_config_file_details_after_delete_org}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.sanity
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
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
        latest_config_file_details_before_create_org = collector.get_the_latest_config_file_details()

    with new_organization_without_user_context(management=management) as new_org:
        with TEST_STEP("STEP - Validate collector received a new full config file that related to the create organization action"):
            collector.wait_for_new_config_file(latest_config_file_details=latest_config_file_details_before_create_org)
            latest_config_file_details_after_create_org = collector.get_the_latest_config_file_details()
            assert not is_config_file_is_partial(config_file_details=latest_config_file_details_after_create_org), \
                f"Config file after creating {new_org} is not full, these are the details\
                {latest_config_file_details_after_create_org}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
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
            latest_config_file_details_before_restart_mng = collector_agent.get_the_latest_config_file_details()
            logger.info(f"restart management {management}")
            management.restart_service()

        with TEST_STEP("STEP - Validate service is up and the collector is running"):
            ManagementUtils.wait_till_operational(management=management)
            collector_agent.wait_until_agent_running()
            rest_collector.wait_until_running()

        with TEST_STEP("STEP - Validate collector received a new full config file that related to the restart action"):
            collector.wait_for_new_config_file(latest_config_file_details=latest_config_file_details_before_restart_mng)
            latest_config_file_details_after_restart_mng = collector.get_the_latest_config_file_details()
            assert not is_config_file_is_partial(config_file_details=latest_config_file_details_after_restart_mng), \
                f"Config file after restart management is not full, these are the details: \
                {latest_config_file_details_after_restart_mng}"


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
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
            latest_config_file_details_before_restart_agg = collector_agent.get_the_latest_config_file_details()
            logger.info(f"restart aggregator {aggregator}")
            aggregator.restart_service()

        with TEST_STEP("STEP - Validate aggregator service is up and the collector is running"):
            aggregator.wait_until_service_will_be_in_desired_state(desired_state=FortiEdrSystemState.RUNNING)
            collector_agent.wait_until_agent_running()
            rest_collector.wait_until_running()

        with TEST_STEP("STEP - Validate collector received a new full config file that related to the restart action"):
            collector.wait_for_new_config_file(latest_config_file_details=latest_config_file_details_before_restart_agg)
            latest_config_file_details_after_restart_agg = collector.get_the_latest_config_file_details()
            assert not is_config_file_is_partial(config_file_details=latest_config_file_details_after_restart_agg), \
                f"Config file after restart aggregator is not full, these are the details: \
                {latest_config_file_details_after_restart_agg}"
