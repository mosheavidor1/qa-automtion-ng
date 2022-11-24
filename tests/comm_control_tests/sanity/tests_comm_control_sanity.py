import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP
from infra.api.management_api.comm_control_policy import CommControlPoliciesNames
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.communication_control_utils.comm_control_app_utils import CommControlAppUtils, \
    setup_comm_control_winscp_env_context, WinscpDetails, WINSCP_SUPPORTED_VERSIONS_DETAILS, \
    install_uninstall_winscp_context


@allure.epic("Management")
@allure.feature("Communication control")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.communication_control_app
@pytest.mark.communication_control_sanity
@pytest.mark.xray('EN-79370')
def test_that_blocking_the_communication_of_a_specific_version_is_not_blocked_all_the_versions_in_windows_os(
        fx_system_without_winscp_app):
    """
         Install 2 different versions of the same app and test that blocking the communication of one specific version
         is not blocked the communication of the second version and check that it indeed blocked the communication only
         of the relevant version

           1. Setup comm control winscp env that includes:
                * Validate that the collector is in the default group and that this group is assigned to the 'Default
                  Communication Control Policy'
                * Install different versions of WinSCP
                * Check if different versions of application winSCP appears in Communication Control applications
                  and validate that the permission of 'Default Communication Control Policy' is `Allow`
                * Check that 'WinSCP' app can connect to management successful
           2. Set 'Default Communication Control Policy' to Prevention mode
           3. Set the 'WinSCP' app, in one version to ‘deny’ and the other to ‘allow’
           4. Validate that WinSCP denied version is actually blocked and cannot connect to remote server (management)
    """
    management, collector = fx_system_without_winscp_app
    assert isinstance(collector, WindowsCollector), "This test only supports windows collector"

    user = management.tenant.default_local_admin
    factory_comm_control_policy = user.rest_components.comm_control_policies
    policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
    default_comm_control_policy = factory_comm_control_policy.get_policy_by_name(policy_name=policy_name)
    allowed_winscp_version_details: WinscpDetails = WINSCP_SUPPORTED_VERSIONS_DETAILS[0]
    denied_winscp_version_details: WinscpDetails = WINSCP_SUPPORTED_VERSIONS_DETAILS[1]

    assert allowed_winscp_version_details.version != denied_winscp_version_details.version, "Bug in test!- The test " \
        "have to install 2 different versions of app - expected different version - we got the same versions"

    with setup_comm_control_winscp_env_context(management=management, collector=collector)as winscp_apps:
        allowed_winscp_app, denied_winscp_app = winscp_apps
        with TEST_STEP(f"STEP- Set '{policy_name}' to Prevention mode"):
            default_comm_control_policy.set_to_prevention_mode(safe=True)

        with TEST_STEP(f"STEP- Set the 'WinSCP' app, in one version to ‘deny’ and the other to ‘allow’"):
            allowed_winscp_app.allow_policy(policy_name=policy_name, safe=True)
            denied_winscp_app.deny_policy(policy_name=policy_name, safe=True)

        with TEST_STEP(f"STEP- Validate that WinSCP denied version is actually blocked and cannot connect to "
                       f"remote server (management)"):
            assert not CommControlAppUtils.is_winscp_can_connect_to_management(collector=collector,
                                                                               version_details=
                                                                               denied_winscp_version_details),\
                f"Bug!!- The app {denied_winscp_app} was not blocked despite the fact that it's permission is" \
                f" 'Deny'"
            assert CommControlAppUtils.is_winscp_can_connect_to_management(collector=collector,
                                                                           version_details=
                                                                           allowed_winscp_version_details), \
                f"Bug!!- The app {allowed_winscp_app} was blocked despite the fact that it's permission is 'Allow'"


@allure.epic("Management")
@allure.feature("Communication control")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.communication_control_app
@pytest.mark.communication_control_sanity
@pytest.mark.xray('EN-79367')
def test_that_comm_control_app_detect_new_installed_app_in_windows_os(fx_system_without_winscp_app):
    """
       Test that after installing an app it appears in Communication Control applications

           1. Validate that the collector is in the default group and that this group is assigned to the 'Default
              Communication Control Policy'
           2. Install WinSCP app on collector
           3. Check if WinSCP app appears in Communication Control applications
    """
    management, collector = fx_system_without_winscp_app
    assert isinstance(collector, WindowsCollector), "This test only supports windows collector"
    tenant = management.tenant
    winscp_app_details = WINSCP_SUPPORTED_VERSIONS_DETAILS[0]

    with TEST_STEP(f"STEP- Check that collector in the default group and that this group is assigned to the default "
                   f" control policy"):
        CommControlAppUtils.validate_default_comm_control_policy_assigned_to_default_collector_group_with_collector(
             collector=collector, tenant=tenant)

    with install_uninstall_winscp_context(management=management,
                                          collector=collector,
                                          versions_details=[winscp_app_details],
                                          connect=False):
        with TEST_STEP(f"STEP- Check if '{winscp_app_details.name}' app appears in Communication Control applications"):
            CommControlAppUtils.wait_until_app_cluster_appear_in_comm_control_apps(app_name=winscp_app_details.name,
                                                                                   tenant=tenant)
