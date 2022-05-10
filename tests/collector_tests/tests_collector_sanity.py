import allure
import pytest

from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.collector_utils import CollectorUtils
from tests.utils.linux_collector_utils import LinuxCollectorUtils
from infra.allure_report_handler.reporter import Reporter, TEST_STEP, INFO
from infra.system_components.collectors.collectors_common_utils import (
    wait_for_running_collector_status_in_mgmt,
    wait_for_disconnected_collector_status_in_mgmt,
    wait_for_running_collector_status_in_cli
)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.linux_sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
@pytest.mark.xray('EN-73287')
def test_stop_start_collector(management, collector):
    """
    1. Stop a running collector and validate it stopped.
    2. Start collector and validate it started successfully.
    """
    with TEST_STEP(f"Stop {collector} and validate"):
        collector.stop_collector(password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} stopped successfully:", INFO)
        CollectorUtils.wait_for_service_down_status_in_cli(collector)
        wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with TEST_STEP(f"Start {collector} and validate"):
        collector.start_collector()
        Reporter.report(f"Validate {collector} started successfully:", INFO)
        wait_for_running_collector_status_in_cli(collector)
        wait_for_running_collector_status_in_mgmt(management, collector)


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.linux_sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
@pytest.mark.xray('EN-73912')
def test_reboot_collector(management, collector):
    """
    1. Reboot the machine and wait until it is reachable after reboot.
    2. Validate that collector is in status 'running' in management and via cli.
    """
    with TEST_STEP(f"Reboot the machine and wait until is reachable:"):
        collector.reboot()

    with TEST_STEP(f"Validate that {collector} is running:"):
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

    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"

    with allure.step(f"Uninstall {collector} and validate"):
        version_before_uninstall = collector.get_version()
        collector.uninstall_collector(registration_password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} uninstalled successfully:")
        assert not collector.is_collector_files_exist(), f"Installation folder contains files, should be empty"
        wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Install {collector} and validate"):
        collector.install_collector(version=collector.details.version,
                                    aggregator_ip=aggregator.host_ip,
                                    organization=management.tenant.organization,
                                    registration_password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} installed successfully:")
        wait_for_running_collector_status_in_mgmt(management, collector)
        wait_for_running_collector_status_in_cli(collector)
        assert collector.get_version() == version_before_uninstall, \
            f"{collector} version is {collector.get_version()} instead of {version_before_uninstall}"


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.linux_sanity
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

    assert isinstance(collector, LinuxCollector), "This test should run only on linux collector"

    with allure.step(f"Before uninstalling {collector}, prepare the installer file:"):
        version_before_uninstall = collector.get_version()
        package_name_before_uninstall = collector.get_package_name()

    with allure.step(f"Uninstall {collector} and validate:"):
        uninstall_output = collector.uninstall_collector(registration_password=management.tenant.registration_password)
        Reporter.report(f"Validate {collector} uninstalled successfully:")
        LinuxCollectorUtils.validate_uninstallation_cmd_output(uninstall_output, collector)
        Reporter.report(f"Validate that {collector} installation folder & installed package removed:")
        assert not collector.is_collector_files_exist(), f"Installation folder was not deleted"
        package_name_after_uninstall = collector.get_package_name()
        assert package_name_after_uninstall is None, \
            f"Collector package was not deleted from OS, name: '{package_name_after_uninstall}'"
        wait_for_disconnected_collector_status_in_mgmt(management, collector)

    with allure.step(f"Install {collector} & Configure"):
        collector.install_collector(version=version_before_uninstall,
                                    aggregator_ip=aggregator.host_ip,
                                    organization=management.tenant.organization,
                                    registration_password=management.tenant.registration_password)

    with allure.step(f"Validate {collector} installed and configured successfully:"):
        Reporter.report(f"Validate {collector} installation folder & installed package name:")
        assert collector.is_collector_files_exist(), f"Installation folder was not created"
        installed_package_name = collector.get_package_name()
        assert installed_package_name == package_name_before_uninstall, \
            f"{collector} Package name is '{installed_package_name}' instead of '{package_name_before_uninstall}'"
        Reporter.report(f"Validate {collector} version:")
        assert collector.get_version() == version_before_uninstall, \
            f"{collector} version is {collector.get_version()} instead of {version_before_uninstall}"
        Reporter.report(f"Validate {collector} status in MGMT and in CLI:")
        wait_for_running_collector_status_in_cli(collector)
        wait_for_running_collector_status_in_mgmt(management, collector)

