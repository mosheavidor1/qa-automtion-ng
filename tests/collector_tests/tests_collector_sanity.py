import allure
import pytest
from tests.utils.collector_utils import CollectorUtils
from tests.utils.linux_collector_utils import LinuxCollectorUtils
from tests.utils.test_utils import TestUtils
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.collectors.collectors_common_utils import (
    wait_for_running_collector_status_in_mgmt,
    wait_for_disconnected_collector_status_in_mgmt,
    wait_for_running_collector_status_in_cli
)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
@pytest.mark.xray('EN-73287')
def test_stop_start_collector(management, collector):
    """
    1. Stop a running collector and validate it stopped.
    2. Start collector and validate it started successfully.
    """
    with allure.step(f"Stop {collector} and validate"):
        collector.stop_collector(password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} stopped successfully:")
        CollectorUtils.wait_for_service_down_status_in_cli(collector)
        wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Start {collector} and validate"):
        collector.start_collector()
        Reporter.report(f"Validate {collector} started successfully:")
        wait_for_running_collector_status_in_cli(collector)
        wait_for_running_collector_status_in_mgmt(management, collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
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
        wait_for_running_collector_status_in_cli(collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.xray('EN-70422')
def test_uninstall_install_windows_collector(management, aggregator, collector):
    """
        This test is going to uninstall and install collector (same version)
        Test steps:
        1. uninstall collector
        2. validate that installation folder is empty
        3. validate no pid for collector + collector status in MGMT is disconnected
        4. install collector with the same version
        5. validate that pid exists + collector status in MGMT & CLI is running
        6. validate that the new installed version is same as before the uninstallation
    """

    with allure.step(f"Uninstall {collector} and validate"):
        version_before_uninstall = collector.get_version()
        uninstallation_log_path = CollectorUtils.create_logs_path(collector, "uninstall_logs")
        with TestUtils.append_log_to_report_on_failure_context(collector, uninstallation_log_path):
            collector.uninstall_collector(registration_password=management.tenant.registration_password, logs_path=uninstallation_log_path)
            Reporter.report(f"Validate {collector} uninstalled successfully:")
            assert collector.is_installation_folder_empty(), f"Installation folder contains files, should be empty"
            wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Install {collector} and validate"):
        installation_log_path = CollectorUtils.create_logs_path(collector, "install_logs")
        with TestUtils.append_log_to_report_on_failure_context(collector, installation_log_path):
            collector.install_collector(version=collector.details.version,
                                        aggregator_ip=aggregator.host_ip,
                                        organization=management.tenant.organization,
                                        registration_password=management.tenant.registration_password,
                                        logs_path=installation_log_path)
            Reporter.report(f"Validate {collector} installed successfully:")
            wait_for_running_collector_status_in_mgmt(management, collector)
            wait_for_running_collector_status_in_cli(collector)
            assert collector.get_version() == version_before_uninstall, \
                f"{collector} version is {collector.get_version()} instead of {version_before_uninstall}"


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.collector_linux_sanity
@pytest.mark.xray('EN-69548')
def test_uninstall_install_configure_linux_collector(management, aggregator, collector):
    """
    http://confluence.ensilo.local/display/ER/Linux+Collector+v5.1
        This test is going to uninstall & install & configure a linux collector.
        1. Stop & uninstall collector
        2. validate that fortiEDR package is not installed + validate installation folder does not exist
        3. validate no pid for collector + collector status in MGMT is disconnected
        4. Install collector with the same version
        5. Configure the installed collector
        6. validate that fortiEDR package is installed + validate that installation folder exists
        7. validate that pid exists + collector status in MGMT & CLI is running
        8. validate that the new installed version is same as before the uninstallation
    """
    with allure.step(f"Before uninstalling {collector}, prepare the installer file:"):
        version_before_uninstall = collector.get_version()
        package_name_before_uninstall = collector.get_package_name()
        installer_path = collector.prepare_version_installer_file(collector_version=version_before_uninstall)

    with allure.step(f"Uninstall {collector} and validate:"):
        uninstall_output = collector.uninstall_collector(registration_password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} uninstalled successfully:")
        LinuxCollectorUtils.validate_uninstallation_cmd_output(uninstall_output, collector)
        Reporter.report(f"Validate that {collector} installation folder & installed package removed:")
        assert not collector.is_installation_folder_exists(), f"Installation folder was not deleted"
        package_name_after_uninstall = collector.get_package_name()
        assert package_name_after_uninstall is None, \
            f"Collector package was not deleted from OS, name: '{package_name_after_uninstall}'"
        wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Install {collector} & Configure"):
        collector.install_collector(installer_path)
        collector.configure_collector(aggregator_ip=aggregator.host_ip,
                                      registration_password=management.tenant.registration_password,
                                      organization=management.tenant.organization)

    with allure.step(f"Validate {collector} installed and configured successfully:"):
        Reporter.report(f"Validate {collector} installation folder & installed package name:")
        assert collector.is_installation_folder_exists(), f"Installation folder was not created"
        installed_package_name = collector.get_package_name()
        assert installed_package_name == package_name_before_uninstall, \
            f"{collector} Package name is '{installed_package_name}' instead of '{package_name_before_uninstall}'"
        Reporter.report(f"Validate {collector} version:")
        assert collector.get_version() == version_before_uninstall, \
            f"{collector} version is {collector.get_version()} instead of {version_before_uninstall}"
        Reporter.report(f"Validate {collector} status in MGMT and in CLI:")
        wait_for_running_collector_status_in_cli(collector)
        wait_for_running_collector_status_in_mgmt(management, collector)

