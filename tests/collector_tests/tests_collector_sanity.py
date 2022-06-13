import allure
import pytest
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.linux_collector_utils import LinuxCollectorUtils
from infra.allure_report_handler.reporter import Reporter, TEST_STEP, INFO
from tests.utils.tenant_utils import new_tenant_context


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
    tenant = management.tenant
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    with TEST_STEP(f"Stop {collector_agent} and validate"):
        collector_agent.stop_collector(password=tenant.organization.registration_password)
        Reporter.report(f"Validate {collector_agent} stopped successfully:", INFO)
        collector_agent.wait_until_agent_down()
        rest_collector.wait_until_disconnected()

    with TEST_STEP(f"Start {collector_agent} and validate"):
        collector_agent.start_collector()
        Reporter.report(f"Validate {collector_agent} started successfully:", INFO)
        collector_agent.wait_until_agent_running()
        rest_collector.wait_until_running()


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
    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    with TEST_STEP(f"Reboot the machine and wait until is reachable:"):
        collector_agent.reboot()

    with TEST_STEP(f"Validate that {collector_agent} is running:"):
        rest_collector.wait_until_running()
        collector_agent.wait_until_agent_running()


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
    tenant = management.tenant
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    collector_version = rest_collector.get_version(from_cache=True)
    with TEST_STEP(f"Uninstall {collector_agent} and validate"):
        version_before_uninstall = collector_agent.get_version()
        password = tenant.organization.registration_password
        collector_agent.uninstall_collector(registration_password=password)
        Reporter.report(f"Validate {collector_agent} uninstalled successfully:")
        assert not collector_agent.is_collector_files_exist(), f"Installation folder contains files, should be empty"
        rest_collector.wait_until_disconnected()

    with TEST_STEP(f"Install {collector_agent} and validate"):
        collector_agent.install_collector(version=collector_version,
                                          aggregator_ip=aggregator.host_ip,
                                          organization=tenant.organization.get_name(),
                                          registration_password=tenant.organization.registration_password)
        Reporter.report(f"Validate {collector_agent} installed successfully:")
        rest_collector.wait_until_running()
        collector_agent.wait_until_agent_running()
        assert collector_agent.get_version() == version_before_uninstall, \
            f"{collector_agent} version is {collector_agent.get_version()} instead of {version_before_uninstall}"


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
    tenant = management.tenant
    collector_agent = collector
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)

    with TEST_STEP(f"Before uninstalling {collector_agent}, prepare the installer file:"):
        version_before_uninstall = collector_agent.get_version()
        package_name_before_uninstall = collector_agent.get_package_name()

    with TEST_STEP(f"Uninstall {collector_agent} and validate:"):
        uninstall_output = collector_agent.uninstall_collector(registration_password=tenant.organization.registration_password)
        Reporter.report(f"Validate {collector_agent} uninstalled successfully:")
        LinuxCollectorUtils.validate_uninstallation_cmd_output(uninstall_output, collector_agent)
        Reporter.report(f"Validate that {collector_agent} installation folder & installed package removed:")
        assert not collector_agent.is_collector_files_exist(), f"Installation folder was not deleted"
        package_name_after_uninstall = collector_agent.get_package_name()
        assert package_name_after_uninstall is None, \
            f"Collector package was not deleted from OS, name: '{package_name_after_uninstall}'"
        rest_collector.wait_until_disconnected()

    with TEST_STEP(f"Install {collector_agent} & Configure"):
        collector_agent.install_collector(version=version_before_uninstall,
                                          aggregator_ip=aggregator.host_ip,
                                          organization=tenant.organization.get_name(),
                                          registration_password=tenant.organization.registration_password)

    with TEST_STEP(f"Validate {collector_agent} installed and configured successfully:"):
        Reporter.report(f"Validate {collector_agent} installation folder & installed package name:")
        assert collector_agent.is_collector_files_exist(), f"Installation folder was not created"
        installed_package_name = collector_agent.get_package_name()
        assert installed_package_name == package_name_before_uninstall, \
            f"{collector_agent} Package name is '{installed_package_name}' instead of '{package_name_before_uninstall}'"
        Reporter.report(f"Validate {collector_agent} version:")
        assert collector_agent.get_version() == version_before_uninstall, \
            f"{collector_agent} version is {collector_agent.get_version()} instead of {version_before_uninstall}"
        Reporter.report(f"Validate {collector_agent} status in MGMT and in CLI:")
        collector_agent.wait_until_agent_running()
        rest_collector.wait_until_running()


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.linux_sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
@pytest.mark.xray('EN-57176')
def test_disable_enable_collector(management, collector):
    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)

    with TEST_STEP(f"Disable {rest_collector} via MGMT and validate status in CLI (Agent) and in MGMT"):
        rest_collector.disable()
        collector_agent.wait_until_agent_disabled()
        rest_collector.wait_until_disabled()

    with TEST_STEP(f"Enable {rest_collector} via MGMT and validate status in CLI and in MGMT"):
        rest_collector.enable()
        collector_agent.wait_until_agent_running()
        rest_collector.wait_until_running()


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.linux_sanity
@pytest.mark.collector_sanity
@pytest.mark.collector_linux_sanity
def test_collector_with_new_org_registration_password(management, collector):
    """ Check that collector can work with the new registration password of the new tenant:
    1. Create new tenant with registration password that is different from the
    registration password of the current tenant.
    2. Move collector to the new tenant.
    3. Stop collector with the new registration password (of the new tenant) and validate that stopped successfully.
    4. Cleanup: start collector -> move collector back to source tenant -> delete the new tenant
    """
    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    old_registration_password = management.tenant.organization.registration_password

    Reporter.report("Create a new tenant with a different registration password", INFO)
    with new_tenant_context(management=management, rest_collector=rest_collector) as tenant_with_collector:
        new_tenant, new_tenant_rest_collector = tenant_with_collector

        with TEST_STEP(f"Stop {collector_agent} with the new registration password and validate that stopped"):
            new_registration_password = new_tenant.organization.registration_password
            assert new_registration_password != old_registration_password
            collector_agent.stop_collector(password=new_registration_password)
            Reporter.report(f"Validate {collector_agent} stopped successfully with new registration password", INFO)
            collector_agent.wait_until_agent_down()
            new_tenant_rest_collector.wait_until_disconnected()

        with TEST_STEP(f"Turn back on the {collector_agent}"):
            collector_agent.start_collector()
            collector_agent.wait_until_agent_running()
            new_tenant_rest_collector.wait_until_running()
