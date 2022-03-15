import allure
import pytest
from tests.utils.collector_utils import CollectorUtils
from tests.utils.test_utils import TestUtils
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.collectors.collectors_common_utils import wait_for_running_collector_status_in_mgmt


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.xray('EN-73287')
def test_stop_start_collector(management, collector):
    """
    1. Stop a running collector and validate it stopped.
    2. Start collector and validate it started successfully.
    """
    with allure.step(f"Stop {collector} and validate"):
        collector.stop_collector()
        Reporter.report(f"Validate {collector} stopped successfully:")
        CollectorUtils.wait_for_service_down_status_in_cli(collector)
        CollectorUtils.wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Start {collector} and validate"):
        collector.start_collector()
        Reporter.report(f"Validate {collector} started successfully:")
        # CollectorUtils.wait_for_running_collector_status_in_cli(collector)
        wait_for_running_collector_status_in_mgmt(management, collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.xray('EN-70422')
def test_install_uninstall_collector(management, collector):
    """
        This test is going to uninstall and install collector (same version)
        Test steps:
        1. uninstall collector
        2. validate that fortiEDR services are not exist
        3. validate installation path is empty and all files were removed
        4. install collector with the same version
        5. check the collector is up and running
    """

    with allure.step(f"Uninstall {collector} and validate"):
        uninstallation_log_path = CollectorUtils.create_logs_path(collector, "uninstall_logs")
        with TestUtils.append_log_to_report_on_failure_context(collector, uninstallation_log_path):
            collector.uninstall_collector(uninstallation_log_path)
            Reporter.report(f"Validate {collector} uninstalled successfully:")
            assert collector.is_installation_folder_empty(), f"Installation folder contains files, should be empty"
            CollectorUtils.wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Install {collector} and validate"):
        installation_log_path = CollectorUtils.create_logs_path(collector, "install_logs")
        with TestUtils.append_log_to_report_on_failure_context(collector, installation_log_path):
            collector.install_collector(version=collector.details.version,
                                        aggregator_ip=management.aggregators[0].host_ip,
                                        logs_path=installation_log_path)
            Reporter.report(f"Validate {collector} installed successfully:")
            wait_for_running_collector_status_in_mgmt(management, collector)
            CollectorUtils.wait_for_running_collector_status_in_cli(collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.xray('EN-73912')
def test_reboot_collector(management, collector):
    """
    1. Reboot the machine and wait until it is reachable after reboot.
    2. Validate that collector is in status 'running' in management and via cli.
    """
    with allure.step(f"Reboot the machine and wait until is reachable:"):
        collector.reboot()

    with allure.step(f"Validate that {collector} is running:"):
        wait_for_running_collector_status_in_mgmt(management, collector)
        CollectorUtils.wait_for_running_collector_status_in_cli(collector)
