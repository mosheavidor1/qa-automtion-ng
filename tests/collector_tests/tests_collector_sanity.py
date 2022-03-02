import allure
import pytest
from tests.utils.collector_utils import CollectorUtils
from tests.utils.test_utils import TestUtils
from infra.allure_report_handler.reporter import Reporter


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.xray('EN-73287')
def test_stop_start_collector(management, collector):
    """
    1. Stop a running collector and validate it stopped.
    2. Start collector and validate it started successfully.
    """
    with allure.step(f"Stop {collector} and validate"):
        collector.stop_collector()
        CollectorUtils.validate_collector_stopped(collector)

    with allure.step(f"Start {collector} and validate"):
        collector.start_collector()
        # CollectorUtils.wait_for_running_collector_status_in_cli(collector)
        CollectorUtils.wait_for_running_collector_status_in_mgmt(management, collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
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
            process_id = collector.get_current_process_id()
            assert process_id is None, f"{collector} is still alive with pid: {process_id}"
            CollectorUtils.validate_installation_folder_is_empty(collector)

    with allure.step(f"Install {collector} and validate"):
        installation_log_path = CollectorUtils.create_logs_path(collector, "install_logs")
        with TestUtils.append_log_to_report_on_failure_context(collector, installation_log_path):
            collector.install_collector(version=collector.details.version,
                                        aggregator_ip=management.aggregators[0].host_ip,
                                        logs_path=installation_log_path)
            Reporter.report(f"Validate {collector} installed successfully:")
            process_id = collector.get_current_process_id()
            assert process_id is not None, f"{collector} is not alive with pid: {process_id}"
            CollectorUtils.wait_for_running_collector_status_in_cli(collector)
            CollectorUtils.wait_for_running_collector_status_in_mgmt(management, collector)
