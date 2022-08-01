import logging
import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.collector_utils import isolate_collector_context, remove_collector_from_isolation_mode, \
    is_config_file_is_partial

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
    1. Isolate collector and Fetch the latest config ,before removing isolation
    2. Remove collector from isolation mode
    3. Validate the collector received partial configuration file (by file size)
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"
    tenant = management.tenant

    with isolate_collector_context(tenant=tenant, collector_agent=collector):
        with TEST_STEP(f"STEP-Isolate collector and Fetch the latest config ,before removing isolation"):
            Reporter.report("Fetch config files before remove from isolation, in order to validate later the diff \
                            after remove from isolation", INFO)
            current_latest_config_file = collector.get_the_latest_config_file_details()

    with TEST_STEP("STEP-Validate collector received a new partial config file that related to the remove isolation action"):
        collector.wait_for_new_config_file(latest_config_file_details=current_latest_config_file)
        latest_config_file_details_after_remove_isolation = collector.get_the_latest_config_file_details()
        assert is_config_file_is_partial(config_file_details=latest_config_file_details_after_remove_isolation), \
            f"Config file after remove isolation collector is not partial, these are the details \n {latest_config_file_details_after_remove_isolation}"
