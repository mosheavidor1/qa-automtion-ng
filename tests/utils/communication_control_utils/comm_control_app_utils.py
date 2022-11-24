from infra.allure_report_handler.reporter import Reporter
from infra.api.management_api.base_comm_control_app import ApplicationPolicyAction
from infra.multi_tenancy.tenant import Tenant
from infra.common_utils import wait_for_condition
from infra.multi_tenancy.tenant import DEFAULT_COLLECTOR_GROUP_NAME
import allure
from infra.api.management_api.collector_group import PolicyDefaultCollectorGroupsNames
from infra.api.management_api.comm_control_app import CommControlApp
from infra.api.management_api.comm_control_policy import CommControlPoliciesNames
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.management import Management
from sut_details import linux_user_name, linux_password, management_host
from enum import Enum
from tests.utils.communication_control_utils.comm_control_policy_utils import change_comm_control_policy_mode_context
from infra.api.management_api.comm_control_app_versions_cluster import CommControlAppVersionsCluster
import logging
from contextlib import contextmanager
from typing import List
import third_party_details

logger = logging.getLogger(__name__)

EMPTY_HTML = "<html><head></head><body></body></html>"
SITE_PARTIAL_TXT = "This domain is for use in illustrative examples in documents"
SITE_TITLE = "<title>Example Domain</title>"
CHROME_APP_NAME = "Google Chrome"
BLOCKED_SITE_ERR = "unknown error: net::ERR_NETWORK_ACCESS_DENIED"
GET_SITE_HTML_EXE_FULL_NAME = "get_dummy_site_html_107.exe"
MAX_WAIT_FOR_APP_CLUSTER_TO_APPEAR = 60
INTERVAL = 5
WINSCP_LOGS_FOLDER_PATH = r"C:\qa"
APPS_SHARED_FOLDER_PATH = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\Apps'
APPS_WITH_CVE_SHARED_FOLDER_PATH = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\Apps_with_CVE'
SUCCESS_CONNECT_WINSCP = "Started a shell/command"
FAILED_CONNECT_WINSCP = "Permission denied"
MAX_WAIT_FOR_APP_TO_INSTALL = 120
MAX_WAIT_FOR_APP_TO_UNINSTALL = 30
MAX_WAIT_FOR_APP_VULNERABILITY = 10 * 60


class AppsNames(Enum):
    winscp = 'WinSCP'
    FIREFOX = "Firefox"


class AppsVulnerabilities(Enum):
    CRITICAL = 'Critical'
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    UNKNOWN = 'Unknown'


class WinscpDetails:
    def __init__(self, version, setup_exe_name, installation_folder_path):
        self.name = AppsNames.winscp.value
        self.version = version
        self.setup_exe_name = setup_exe_name
        self.installation_folder_path = rf"{installation_folder_path}\{self.name}"
        self.uninstall_exe_name = 'unins000.exe'
        self.log_path = rf"{self.name}-{self.version}-log.txt"

    def __repr__(self):
        return f"{self.name} app in version '{self.version}'"


WINSCP_SUPPORTED_VERSIONS_DETAILS = [WinscpDetails(version='5.20.3.12378',
                                                   setup_exe_name='WinSCP-5.20.3.RC-Setup.exe',
                                                   installation_folder_path=rf'C:\Users\ensilo\AppData\Local\Programs'),
                                     WinscpDetails(version='5.19.6.12002',
                                                   setup_exe_name='WinSCP-5.19.6-Setup.exe',
                                                   installation_folder_path=rf'C:\Users\ensilo\Downloads')]


@contextmanager
def setup_comm_control_winscp_env_context(management: Management, collector: CollectorAgent) -> List[CommControlApp]:
    """
        Context for setup comm control winscp env:
            1. Validate that the collector is in the default group and that this group is assigned to the 'Default
               Communication Control Policy'
            2. Install different versions of WinSCP
            3. Check if different versions of application winSCP appears in Communication Control applications
               and validate that the permission of 'Default Communication Control Policy' is `Allow`
            4. Check that 'WinSCP' app can connect to management successful
    """
    user = management.tenant.default_local_admin
    factory_comm_control_app = user.rest_components.comm_control_app
    factory_comm_control_policy = user.rest_components.comm_control_policies
    policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
    default_comm_control_policy = factory_comm_control_policy.get_policy_by_name(policy_name=policy_name)
    winscp_apps: List[CommControlApp] = []

    with Reporter.allure_step_context("Setup: Check that collector in the default group and that this group is assigned"
                                      " to the default control policy", logger_func=logger.info):
        CommControlAppUtils.validate_default_comm_control_policy_assigned_to_default_collector_group_with_collector(
            collector=collector, tenant=management.tenant)

    with install_uninstall_winscp_context(management=management,
                                          collector=collector, versions_details=WINSCP_SUPPORTED_VERSIONS_DETAILS):
        with Reporter.allure_step_context(f"Setup: Check if different versions of winSCP app appears in Communication "
                                          f"Control applications, and validate that the permission of policy "
                                          f"'{policy_name}' is `Allow`", logger_func=logger.info):
            for version_details in WINSCP_SUPPORTED_VERSIONS_DETAILS:
                CommControlAppUtils.wait_until_app_version_appear_in_comm_control_apps(
                    app_name=version_details.name, version=version_details.version,
                    tenant=management.tenant)
                winscp_app = factory_comm_control_app.get_app(app_name=version_details.name, version=version_details.
                                                              version,
                                                              safe=True)
                winscp_apps.append(winscp_app)
                assert winscp_app is not None, f"ERROR - {version_details} does not appear in communication control " \
                                               f"applications"
                assert winscp_app.get_policy_permission(policy_name=policy_name) == ApplicationPolicyAction.ALLOW.value, \
                    f"Bug- the default permission of policy '{policy_name}' in {version_details} should be " \
                    f"{ApplicationPolicyAction.ALLOW.value}"

        with Reporter.allure_step_context(f"Setup: Check that 'WinSCP' app can connect to management successfully",
                                          logger_func=logger.info):
            for version_details in WINSCP_SUPPORTED_VERSIONS_DETAILS:
                assert CommControlAppUtils.is_winscp_can_connect_to_management(collector=collector,
                                                                               version_details=version_details), \
                    f"Bug in env!! - Management is unstable, {version_details} cannot connect to it"
        with change_comm_control_policy_mode_context(comm_control_policy=default_comm_control_policy):
            with change_apps_permission_default_comm_control_policy_context(apps=winscp_apps):
                yield winscp_apps


@contextmanager
def install_uninstall_winscp_context(management: Management, collector: CollectorAgent,
                                     versions_details: list[WinscpDetails],
                                     connect: bool = True):
    """ Context for installing versions of the 'WinSCP' app, it is optional to connect to them after installation,
     finally uninstall them and delete them from management
    """
    assert isinstance(collector, WindowsCollector), "This context only supports windows collector"
    with allure.step(f"Setup - Install WinSCP versions app: {versions_details}"):
        CommControlAppUtils.install_winscp_versions(collector=collector, versions_details=versions_details, connect=connect)
    try:
        yield
    finally:
        with allure.step(f"Cleanup - Uninstall WinSCP app {versions_details} and delete WinSCP app in the management"):
            CommControlAppUtils.uninstall_winscp_versions(collector=collector, versions_details=versions_details)
            CommControlAppUtils.delete_app_from_management(management=management, app_name=AppsNames.winscp.value)


@contextmanager
def install_uninstall_vulnerable_firefox_context(management: Management, collector: CollectorAgent):
    """ Context for installing Firefox vulnerable app version, finally uninstall and delete from management """
    assert isinstance(collector, WindowsCollector), "This context only supports windows collector"
    with allure.step(f"Setup - Install Firefox"):
        CommControlAppUtils.install_vulnerable_firefox(windows_collector=collector)
    try:
        yield
    finally:
        with allure.step("Cleanup - Uninstall Firefox app and delete it also from the management"):
            CommControlAppUtils.uninstall_vulnerable_firefox(windows_collector=collector)
            CommControlAppUtils.delete_app_from_management(management=management, app_name=AppsNames.FIREFOX.value)


@contextmanager
def change_apps_permission_default_comm_control_policy_context(apps: List[CommControlApp]):
    """ Context for return the previous permissions for 'Default Communication Control Policy' for apps """
    policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
    original_permission_by_version = {}
    for app in apps:
        original_permission_by_version[app.version] = app.get_policy_permission(policy_name=policy_name)
    try:
        yield
    finally:
        with allure.step(f"Cleanup - return the previous permissions for policy '{policy_name}' for apps: {apps}"):
            for app in apps:
                app.set_policy_permission(policy_name=policy_name,
                                          permission=original_permission_by_version[app.version], safe=True)


def get_chrome_exe_path(windows_collector: WindowsCollector, safe=False):
    return get_installed_app_exe_path(windows_collector=windows_collector, exe_name="chrome.exe", safe=safe)


def get_firefox_exe_path(windows_collector: WindowsCollector, safe=False):
    return get_installed_app_exe_path(windows_collector=windows_collector, exe_name="firefox.exe", safe=safe)


def get_installed_app_exe_path(windows_collector: WindowsCollector, exe_name, safe=False):
    """ Get the app's exe path only if this app is installed """
    assert exe_name.endswith('.exe'), f"Not .exe extension, got: {exe_name}"
    logger.info(f"Find path of installed {exe_name}")
    cmd = rf"reg query HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\ /s /f \{exe_name} | findstr Default"
    result = windows_collector.os_station.execute_cmd(cmd=cmd, fail_on_err=False, asynchronous=False)
    if result is None or 'C:' not in result:
        assert safe, f"{exe_name} is NOT installed, this is the result of query: \n {result}"
        logger.info(f"{exe_name} is NOT installed, this is the result of query: \n {result}")
        return None
    result = result.split('C:')
    path = f"C:{result[-1]}"
    logger.info(f"'{exe_name}' is installed in: {path}")
    return path


class CommControlAppUtils:

    @staticmethod
    def validate_chrome_windows_collector(windows_collector: WindowsCollector):
        """ Validate that it is a windows collector and chrome is installed """
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        get_chrome_exe_path(windows_collector=windows_collector)

    @staticmethod
    def is_headless_chrome_communication_blocked_by_collector(windows_collector: WindowsCollector):
        """ Use a headless chrome to dump html of specific site via CMD if html is empty so the site is blocked """
        CommControlAppUtils.validate_chrome_windows_collector(windows_collector=windows_collector)
        logger.info(f"Check if headless chrome communication is blocked by {windows_collector}")
        chrome_exe_path = get_chrome_exe_path(windows_collector=windows_collector)
        cmd = rf'"{chrome_exe_path}" --headless --disable-gpu --enable-logging --dump-dom https://www.example.com'
        actual_html = windows_collector.os_station.execute_cmd(cmd=cmd, fail_on_err=False, asynchronous=False)
        if actual_html == EMPTY_HTML:
            logger.info(f"Headless Chrome communication is blocked by {windows_collector}, "
                        f"got this html: \n {actual_html}")
            return True
        assert SITE_PARTIAL_TXT in actual_html and SITE_TITLE in actual_html, \
            f"INFRA BUG, got invalid result:\n {actual_html} \n Check CMD or if chrome is installed on the vm"
        logger.info(f"Headless Chrome communication is NOT blocked by {windows_collector}, "
                    f"got this html: \n {actual_html}")
        return False

    @staticmethod
    def is_chrome_communication_blocked_by_collector(windows_collector: WindowsCollector):
        """ Use an exe that by selenium and chromedriver opens a dummy site example.com,
        if we get html from this site so that means that chrome communication is not blocked.
        See script in infra/scripts/selenium/get_dummy_site_html.py """

        CommControlAppUtils.validate_chrome_windows_collector(windows_collector=windows_collector)
        logger.info(f"Check if chrome browser communication is blocked by {windows_collector}")
        exe_path = _get_selenium_chrome_exe_script_path(windows_collector=windows_collector)
        site_html = windows_collector.os_station.execute_cmd(cmd=exe_path, fail_on_err=False, asynchronous=False,
                                                             use_pa_py_exec_connection=True)
        if BLOCKED_SITE_ERR in site_html:
            assert SITE_PARTIAL_TXT not in site_html, f"INFRA BUG, wrong analyze of html: \n {site_html}"
            logger.info(f"Chrome browser communication is blocked by {windows_collector}, "
                        f"got this html: \n {site_html}")
            return True
        assert SITE_PARTIAL_TXT in site_html and SITE_TITLE in site_html, \
            f"INFRA BUG, can't parse html:\n {site_html} \n Check CMD or if chrome is installed on the vm"
        logger.info(f"Chrome browser communication is NOT blocked by {windows_collector}, "
                    f"got this html: \n {site_html}")
        return False

    @staticmethod
    def add_chrome_to_comm_control_app_cluster(windows_collector: WindowsCollector, tenant: Tenant,
                                               safe=False, timeout=None, interval=None):
        """ Trigger chrome browser via selenium and chromedriver -->
        only after trigger, google chrome will appear in the communication control apps.
        See script in infra/scripts/selenium/get_dummy_site_html.py
        """
        CommControlAppUtils.validate_chrome_windows_collector(windows_collector=windows_collector)
        logger.info("Add chrome browser to communication control apps cluster")
        user = tenant.default_local_admin
        factory_comm_control_app = user.rest_components.comm_control_app
        chrome_comm_control_app_cluster = factory_comm_control_app.get_app_installed_versions_cluster_by_name(
            app_name=CHROME_APP_NAME, safe=True)
        if chrome_comm_control_app_cluster is not None:
            assert safe, f"Google chrome already appear in comm control apps: {chrome_comm_control_app_cluster}"
            logger.info(f"Google chrome already appear in comm control apps: {chrome_comm_control_app_cluster}")
            return chrome_comm_control_app_cluster
        exe_path = _get_selenium_chrome_exe_script_path(windows_collector=windows_collector)
        logger.info("Open and close chrome browse")
        windows_collector.os_station.execute_cmd(cmd=exe_path, fail_on_err=False, asynchronous=False,
                                                 use_pa_py_exec_connection=True)
        CommControlAppUtils.wait_until_app_cluster_appear_in_comm_control_apps(
            app_name=CHROME_APP_NAME, tenant=tenant, timeout=timeout, interval=interval
        )
        chrome_comm_control_app_cluster = factory_comm_control_app.get_app_installed_versions_cluster_by_name(
            app_name=CHROME_APP_NAME, safe=False)
        return chrome_comm_control_app_cluster

    @staticmethod
    def get_vulnerable_firefox_setup_exe_name(windows_collector: WindowsCollector):
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        architecture = windows_collector.os_station.get_os_architecture()
        if architecture == '64-bit':
            vulnerable_firefox_setup_exe_name = "Mozilla_Firefox_(64bit)_v68.0.2.exe"
        elif architecture == '32-bit':
            vulnerable_firefox_setup_exe_name = "Mozilla_Firefox_(32bit)_v68.0.2.exe"
        else:
            raise Exception(f"Not supported {architecture}")
        logger.info(f"Vulnerable firefox setup exe name is: {vulnerable_firefox_setup_exe_name}")
        return vulnerable_firefox_setup_exe_name

    @staticmethod
    def wait_until_app_cluster_appear_in_comm_control_apps(app_name: str, tenant: Tenant, timeout=None, interval=None):
        waiting_msg = f"Wait until app cluster '{app_name}' will appear in comm control apps"
        logger.info(waiting_msg)
        user = tenant.default_local_admin
        factory_comm_control_app = user.rest_components.comm_control_app
        timeout = timeout or MAX_WAIT_FOR_APP_CLUSTER_TO_APPEAR
        interval = interval or INTERVAL

        def condition():
            comm_control_app_cluster = factory_comm_control_app.get_app_installed_versions_cluster_by_name(
                app_name=app_name, safe=True
            )
            return comm_control_app_cluster is not None

        wait_for_condition(condition_func=condition, timeout_sec=timeout,
                           interval_sec=interval, condition_msg=waiting_msg)

    @staticmethod
    def wait_until_app_version_appear_in_comm_control_apps(app_name: str, version: str, tenant: Tenant, timeout=None, interval=None):
        """ Wait for a specific app version to appear in management communication control apps """
        waiting_msg = f"Wait until app '{app_name}' in version '{version}' will appear in comm control apps"
        logger.info(waiting_msg)
        user = tenant.default_local_admin
        factory_comm_control_app = user.rest_components.comm_control_app
        timeout = timeout or MAX_WAIT_FOR_APP_CLUSTER_TO_APPEAR
        interval = interval or INTERVAL

        def condition():
            comm_control_app = factory_comm_control_app.get_app(app_name=app_name, version=version, safe=True)
            return comm_control_app is not None

        wait_for_condition(condition_func=condition, timeout_sec=timeout,
                           interval_sec=interval, condition_msg=waiting_msg)

    @staticmethod
    def wait_until_app_is_installed(windows_collector: WindowsCollector, exe_name, timeout=None, interval=None):
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        assert exe_name.endswith('.exe'), f"Not .exe extension, got: {exe_name}"
        waiting_msg = f"Wait until app '{exe_name}' will be installed"
        logger.info(waiting_msg)
        timeout = timeout or MAX_WAIT_FOR_APP_TO_INSTALL
        interval = interval or INTERVAL

        def condition():
            installed_app_path = get_installed_app_exe_path(windows_collector=windows_collector,
                                                            exe_name=exe_name, safe=True)
            return installed_app_path is not None

        wait_for_condition(condition_func=condition, timeout_sec=timeout,
                           interval_sec=interval, condition_msg=waiting_msg)

    @staticmethod
    def wait_until_app_is_uninstalled(windows_collector: WindowsCollector, exe_name, timeout=None, interval=None):
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        assert exe_name.endswith('.exe'), f"Not .exe extension, got: {exe_name}"
        waiting_msg = f"Wait until app '{exe_name}' will be uninstalled"
        logger.info(waiting_msg)
        timeout = timeout or MAX_WAIT_FOR_APP_TO_UNINSTALL
        interval = interval or INTERVAL

        def condition():
            installed_app_path = get_installed_app_exe_path(windows_collector=windows_collector,
                                                            exe_name=exe_name, safe=True)
            return installed_app_path is None

        wait_for_condition(condition_func=condition, timeout_sec=timeout,
                           interval_sec=interval, condition_msg=waiting_msg)

    @staticmethod
    def wait_for_app_vulnerability(management: Management, app_name,
                                   vulnerability, timeout=None, interval=None):
        tenant = management.tenant
        user = tenant.default_local_admin
        waiting_msg = f"Wait until app '{app_name}' vulnerability is '{vulnerability}'"
        logger.info(waiting_msg)
        timeout = timeout or MAX_WAIT_FOR_APP_VULNERABILITY
        interval = interval or INTERVAL
        comm_control_app_cluster = user.rest_components.comm_control_app.get_app_installed_versions_cluster_by_name(
            app_name=app_name, safe=True)
        assert comm_control_app_cluster is not None, f"{comm_control_app_cluster} not in management comm control apps"

        def condition():
            severity = comm_control_app_cluster.get_severity(from_cache=False)
            return severity.lower() == vulnerability.lower()

        wait_for_condition(condition_func=condition, timeout_sec=timeout,
                           interval_sec=interval, condition_msg=waiting_msg)

    @staticmethod
    def validate_default_comm_control_policy_assigned_to_default_collector_group_with_collector(
            collector: CollectorAgent, tenant: Tenant):
        """Validate that the collector is in the default group and that this group is assigned to the 'Default
        Communication Control Policy'"""
        user = tenant.default_local_admin
        factory_comm_control_policy = user.rest_components.comm_control_policies
        policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
        rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        collector_group_name = rest_collector.get_group_name()
        assert collector_group_name == PolicyDefaultCollectorGroupsNames.DEFAULT_COLLECTOR_GROUP_NAME.value, \
            f"ERROR - The collector is not in the 'default collector group' group "
        default_comm_control_policy = factory_comm_control_policy.get_policy_by_name(policy_name=policy_name)
        assert default_comm_control_policy.is_default_group_assigned(), \
            f"ERROR - Policy '{policy_name}' is not assigned to 'Default Collector Group'"

    @staticmethod
    def install_winscp_versions(collector: CollectorAgent, versions_details: List[WinscpDetails], connect: bool = True):
        """ Installing versions of the 'WinSCP' app, it is optional to connect to them after installation"""
        target_path = collector.get_qa_files_path()
        files_to_copy = [version_details.setup_exe_name for version_details in versions_details]
        logger.info(f"Going to copy files '{files_to_copy}' from shared folder to {target_path}")
        target_folder = collector.os_station.copy_files_from_shared_folder(target_path_in_local_machine=target_path,
                                                                           shared_drive_path=APPS_SHARED_FOLDER_PATH,
                                                                           files_to_copy=files_to_copy)
        for version_details in versions_details:
            logger.info(f"Going to install {version_details.name} app in version {version_details.version} in path "
                        f"'{version_details.installation_folder_path}'")
            collector.os_station.execute_cmd(
                cmd=rf"{target_folder}\\{version_details.setup_exe_name} /VERYSILENT /SUPPRESSMSGBOXES /DIR="
                    rf"{version_details.installation_folder_path}", use_pa_py_exec_connection=True)
            locations_installed_winscp_apps = collector.get_exe_folders_paths_by_name(
                exe_name=f'{version_details.name}.exe')
            assert version_details.installation_folder_path in locations_installed_winscp_apps, \
                f"ERROR!!- The '{version_details.name}' in version {version_details.version} app was not installed " \
                f"successfully"
            if connect:
                CommControlAppUtils.connect_winscp_to_management(collector=collector, version_details=version_details)

    @staticmethod
    def uninstall_winscp_versions(collector: CollectorAgent, versions_details: list[WinscpDetails]):
        """ Uninstalling versions of the 'WinSCP' app """
        for version_details in versions_details:
            logger.info(f"Going to uninstall {version_details.name} app in version {version_details.version}")
            collector.os_station.execute_cmd(
                cmd=rf'{version_details.installation_folder_path}\{version_details.uninstall_exe_name} /VERYSILENT /SUPPRESSMSGBOXES', use_pa_py_exec_connection=True)
            locations_installed_winscp_apps = collector.get_exe_folders_paths_by_name(
                exe_name=f'{version_details.name}.exe')
            assert version_details.installation_folder_path not in locations_installed_winscp_apps, \
                f"ERROR!!- The '{version_details.name}' in version {version_details.version} app was not uninstalled " \
                f"successfully"

    @staticmethod
    def install_vulnerable_firefox(windows_collector: WindowsCollector):
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        vulnerable_firefox_setup_exe_name = CommControlAppUtils.get_vulnerable_firefox_setup_exe_name(windows_collector)
        installed_exe_path = get_firefox_exe_path(windows_collector=windows_collector, safe=True)
        assert installed_exe_path is None, f"Firefox already installed in {installed_exe_path}"
        target_path = windows_collector.get_qa_files_path()
        logger.info(f"Get '{vulnerable_firefox_setup_exe_name}' from shared {APPS_WITH_CVE_SHARED_FOLDER_PATH}")
        target_folder = windows_collector.os_station.copy_files_from_shared_folder(
            target_path_in_local_machine=target_path, shared_drive_path=APPS_WITH_CVE_SHARED_FOLDER_PATH,
            files_to_copy=[vulnerable_firefox_setup_exe_name]
        )
        logger.info(f"Install {vulnerable_firefox_setup_exe_name}")
        setup_cmd = rf'{target_folder}\"{vulnerable_firefox_setup_exe_name}" -ms'
        windows_collector.os_station.execute_cmd(cmd=setup_cmd, fail_on_err=True, use_pa_py_exec_connection=True)
        CommControlAppUtils.wait_until_app_is_installed(windows_collector=windows_collector, exe_name="firefox.exe")

    @staticmethod
    def uninstall_vulnerable_firefox(windows_collector: WindowsCollector):
        assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
        logger.info("Uninstall vulnerable firefox")
        installed_exe_path = get_firefox_exe_path(windows_collector=windows_collector, safe=True)
        assert installed_exe_path is not None, "Firefox is not installed"
        installation_folder_path = installed_exe_path.split(rf"\firefox.exe")[0]
        uninstallation_cmd = rf'"{installation_folder_path}\uninstall\helper.exe" /S'
        windows_collector.os_station.execute_cmd(cmd=uninstallation_cmd, fail_on_err=True, use_pa_py_exec_connection=True)
        CommControlAppUtils.wait_until_app_is_uninstalled(windows_collector=windows_collector, exe_name="firefox.exe")

    @staticmethod
    def delete_app_from_management(management: Management, app_name, safe=False):
        logger.info(f"Delete '{app_name}' cluster versions from communication control apps, via GUI")
        tenant = management.tenant
        user = tenant.default_local_admin
        comm_control_app_cluster = user.rest_components.comm_control_app.get_app_installed_versions_cluster_by_name(
            app_name=app_name, safe=True)
        if comm_control_app_cluster is None:
            assert safe, f"{comm_control_app_cluster} is not in management comm control apps"
            logger.info(f"{comm_control_app_cluster} is not in management comm control apps")
        else:
            management.ui_client.communication_control_app.delete_app_from_management(
                data={"applicationName": app_name})
            logger.info(f"Validate that '{app_name}' cluster versions deleted from communication control apps")
            comm_control_app_cluster = user.rest_components.comm_control_app.get_app_installed_versions_cluster_by_name(
                app_name=app_name, safe=True)
            assert comm_control_app_cluster is None, f"'{app_name}' cluster versions was NOT deleted from communication " \
                                                     f"control apps"

    @staticmethod
    def validate_app_vulnerability_via_gui(management: Management, app_name, vulnerability):
        logger.info(f"Check via gui that the vulnerability of '{app_name}' cluster in comm control is {vulnerability}")
        tenant = management.tenant
        user = tenant.default_local_admin
        comm_control_app_cluster = user.rest_components.comm_control_app.get_app_installed_versions_cluster_by_name(
            app_name=app_name, safe=True)
        assert comm_control_app_cluster is not None, f"{comm_control_app_cluster} not in management comm control apps"
        management.ui_client.communication_control_app.validate_app_vulnerability(
            data={"applicationName": app_name, "vulnerability": vulnerability})
        severity = comm_control_app_cluster.get_severity()
        assert vulnerability.lower() == severity.lower(), f"GUI validation is broken, actual vulnerability: {severity}"

    @staticmethod
    def connect_winscp_to_management(collector: CollectorAgent, version_details: WinscpDetails):
        """ Open a connection session at the WinSCP command line and write the log connection to the log file,
            if the log file exists the command line will override the existing data
        """
        log_folder_path = rf'{WINSCP_LOGS_FOLDER_PATH}\{version_details.log_path}'
        if collector.os_station.is_path_exist(path=log_folder_path):
            collector.os_station.remove_file(file_path=log_folder_path)
        collector.os_station.create_new_folder(folder_path=WINSCP_LOGS_FOLDER_PATH)
        logger.info(f"Going to connect session in {version_details.name} app in version {version_details.version} and "
                    f"write the Log connection to the log file")
        collector.os_station.execute_cmd(
            cmd=rf'{version_details.installation_folder_path}\{version_details.name}.exe sftp://{linux_user_name}:{linux_password}@'
                rf'{management_host}:22 /command /log={log_folder_path} /rawconfig Logging\LogFileAppend=0 /hostkey=*')
        assert collector.os_station.is_path_exist(
            path=log_folder_path), "Bug in infra!, - The connection from winscp to " \
                                   "management failed"

    @staticmethod
    def is_winscp_can_connect_to_management(collector: CollectorAgent, version_details: WinscpDetails) -> bool:
        """ Check that 'WinSCP' app can connect to management successfully
            Find str indicating failed/successful connection in the log file, if there is- the connection is
            failed, If not - the connection was successful
        """
        assert isinstance(collector, WindowsCollector), "This function only supports windows collector"
        logger.info(f"Check if WinSCP can connect to management")
        CommControlAppUtils.connect_winscp_to_management(collector=collector, version_details=version_details)
        log_folder_path = rf'{WINSCP_LOGS_FOLDER_PATH}\{version_details.log_path}'
        logger.info(f"Get file content from path {log_folder_path}")
        content = collector.os_station.get_file_content(file_path=log_folder_path)
        assert content is not None, fr"Bug in infra!- failed to read the log in path '{log_folder_path}'"
        if SUCCESS_CONNECT_WINSCP.lower() in content.lower() and FAILED_CONNECT_WINSCP.lower() not in content.lower():
            return True
        if FAILED_CONNECT_WINSCP.lower() in content.lower():
            return False
        raise Exception(f"Bug in infra, can't parse this log content: \n {content}")


def _get_selenium_chrome_exe_script_path(windows_collector: WindowsCollector):
    """ Getting the desired exe from the shared selenium scripts folder """
    exe_folder_path_in_shared_drive = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\scripts\selenium'
    logger.info(f"Get exe that can fetch site's html: '{GET_SITE_HTML_EXE_FULL_NAME}' "
                f"from {exe_folder_path_in_shared_drive}")
    exe_folder_path_in_local_machine = windows_collector.os_station.copy_files_from_shared_folder(
        target_path_in_local_machine=windows_collector.get_qa_files_path(),
        shared_drive_path=exe_folder_path_in_shared_drive,
        files_to_copy=[GET_SITE_HTML_EXE_FULL_NAME]
    )
    full_exe_path = fr'{exe_folder_path_in_local_machine}\{GET_SITE_HTML_EXE_FULL_NAME}'
    assert windows_collector.os_station.is_path_exist(path=full_exe_path), \
        f"Desired exe: '{GET_SITE_HTML_EXE_FULL_NAME}' FAILED copy to {exe_folder_path_in_local_machine}"
    logger.info(f"'{GET_SITE_HTML_EXE_FULL_NAME}' created in: {full_exe_path}")
    return full_exe_path


@contextmanager
def setup_comm_control_chrome_env_context(windows_collector: WindowsCollector,
                                          management: Management) -> CommControlAppVersionsCluster:
    """ Setup env to test communication control by using chrome app.
    1. Validate that collector is in the default group.
    2. Validate that the default group is assigned to the communication control default policy.
    3. Trigger chrome in order it will appear in the communication control apps list.
    4. Assert that chrome has access to internet.
    5. Delete chrome versions cluster from the communication control apps in management
    """
    CommControlAppUtils.validate_chrome_windows_collector(windows_collector=windows_collector)
    tenant = management.tenant
    user = tenant.default_local_admin
    default_policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=windows_collector.host_ip)

    with allure.step("Setup - Prepare and validate env for working with chrome"):
        default_comm_control_policy = user.rest_components.comm_control_policies.get_policy_by_name(
            policy_name=default_policy_name)
        logger.info(f"Validate that {windows_collector} is in the default group and assigned to default control policy")
        assert rest_collector.get_group_name() == DEFAULT_COLLECTOR_GROUP_NAME, \
            f"Bug in test setup - The collector is not in the default group '{DEFAULT_COLLECTOR_GROUP_NAME}'"
        assert default_comm_control_policy.is_default_group_assigned(), \
            f"Bug in test setup - Policy '{default_policy_name}' is not assigned to '{DEFAULT_COLLECTOR_GROUP_NAME}'"
        logger.info(f"Delete and Add relevant '{CHROME_APP_NAME}' versions cluster to  communication control apps list")
        CommControlAppUtils.delete_app_from_management(app_name=CHROME_APP_NAME, management=management, safe=True)
        chrome_comm_control_app_cluster = CommControlAppUtils.add_chrome_to_comm_control_app_cluster(
            windows_collector, tenant=tenant, safe=False
        )
        logger.info(f"Validate that '{CHROME_APP_NAME}' has access to the network")
        assert not CommControlAppUtils.is_chrome_communication_blocked_by_collector(windows_collector), \
            f"{CHROME_APP_NAME} doesn't have access to the network, can't start the test"
    try:
        yield
    finally:
        with allure.step("Cleanup - clean the chrome env"):
            CommControlAppUtils.delete_app_from_management(app_name=CHROME_APP_NAME, management=management, safe=True)


@contextmanager
def setup_vulnerable_app_firefox_env_context(windows_collector: WindowsCollector, management: Management):
    """ Setup env to test vulnerable app using firefox old 68 version.
    1. Delete firefox versions cluster from the communication control apps in management
    2. Uninstall existing firefox from collector.
    3. Install Firefox vulnerable version in the collector.
    4. Uninstall firefox from collector and delete firefox versions cluster from the comm control apps in management.
    """
    assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
    vulnerable_app_name = AppsNames.FIREFOX.value

    with Reporter.allure_step_context(f"Setup - Uninstall firefox if exists", logger_func=logger.info):
        installed_exe_path = get_firefox_exe_path(windows_collector=windows_collector, safe=True)
        if installed_exe_path is not None:
            logger.info(f"Firefox already installed, uninstall it from: {installed_exe_path}")
            CommControlAppUtils.uninstall_vulnerable_firefox(windows_collector=windows_collector)

    with Reporter.allure_step_context(f"Setup - Prepare env for working with vulnerable app firefox",
                                      logger_func=logger.info):
        logger.info(f"Delete vulnerable app '{vulnerable_app_name}' from communication control apps list")
        CommControlAppUtils.delete_app_from_management(app_name=vulnerable_app_name, management=management, safe=True)

    with install_uninstall_vulnerable_firefox_context(management=management, collector=windows_collector):
        yield
