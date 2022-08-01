import logging
import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.collector_utils import is_config_file_is_partial
from tests.utils.tenant_utils import new_tenant_context

logger = logging.getLogger(__name__)


@allure.epic("Collector Configuration File")
@allure.feature("Collector full configuration file")
@pytest.mark.sanity
@pytest.mark.collector_configuration
@pytest.mark.collector_configuration_sanity
@pytest.mark.xray('EN-76208')
def test_receive_full_configuration_after_delete_organization_in_windows_os(management, collector):
    """
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
