from contextlib import contextmanager
import allure
import pytest
from infra.api.management_api.comm_control_policy import CommControlPoliciesNames
from infra.allure_report_handler.reporter import Reporter, TEST_STEP, INFO
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.api.management_api.security_policy import DefaultPoliciesNames, RulesNames, RuleActions
from infra.multi_tenancy.tenant import DEFAULT_COLLECTOR_GROUP_NAME
from infra.api.management_api.base_policy import ModeNames, RuleStates
from infra.system_components.management import Management
from infra.api.management_api.security_policy import SecurityPolicy
from infra.api.management_api.event import EventActionNames
from tests.utils.policy_utils import get_relevant_malware_name, change_policy_mode_context
from tests.utils.communication_control_utils.comm_control_policy_utils import change_comm_control_policy_mode_context
from tests.utils.collector_utils import wait_till_configuration_drill_down_to_collector
from tests.utils.communication_control_utils.comm_control_app_utils import CommControlAppUtils, CHROME_APP_NAME, \
    setup_comm_control_chrome_env_context, AppsNames, setup_vulnerable_app_firefox_env_context, AppsVulnerabilities
from tests.utils.policy_utils import set_policy_mode_ui
from tests.utils.security_events_utils import validate_event_ui

@allure.epic("POC FLOW")
@allure.feature("Communication control")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.communication_control_app
@pytest.mark.communication_control_sanity
@pytest.mark.poc_flow
@pytest.mark.xray('EN-80508')
def test_block_browser_communication_poc_flow(management, collector):
    """ Because it is part of POC flow this test is GUI oriented.
    Existing bug: EN-79391 happen only when open chrome via GUI
    """
    assert isinstance(collector, WindowsCollector), "Support only a windows collector"
    tenant = management.tenant
    collector_agent = collector
    user = tenant.default_local_admin
    test_im_params = {"applicationName": CHROME_APP_NAME}
    default_policy_name = CommControlPoliciesNames.DEFAULT_COMM_CONTROL_POLICY.value
    default_comm_control_policy = user.rest_components.comm_control_policies.get_policy_by_name(
        policy_name=default_policy_name)

    Reporter.report(f"Setup - set communication control chrome env testing for {collector_agent}", INFO)
    with setup_comm_control_chrome_env_context(collector_agent, management):
        with change_comm_control_policy_mode_context(comm_control_policy=default_comm_control_policy):
            with TEST_STEP("STEP - Set the default comm control policy to prevention mode via GUI"):
                management.ui_client.communication_control_policy.set_default_policy_to_prevention()

            with TEST_STEP(f"STEP - Deny the default comm control policy of '{CHROME_APP_NAME}', via GUI"):
                with wait_till_configuration_drill_down_to_collector(collector_agent=collector_agent):
                    management.ui_client.communication_control_app.deny_app_default_policy(data=test_im_params)

            with TEST_STEP(f"STEP - Validate that '{CHROME_APP_NAME}' communication is blocked by {collector_agent}"):
                is_blocked = CommControlAppUtils.is_chrome_communication_blocked_by_collector(collector_agent)
                assert is_blocked, f"{CHROME_APP_NAME}' communication was not blocked by the {collector_agent}"


@allure.epic("POC FLOW")
@allure.feature("Communication control")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.communication_control_app
@pytest.mark.communication_control_sanity
@pytest.mark.poc_flow
@pytest.mark.fcs_sanity
@pytest.mark.xray('EN-79167')
def test_communication_control_app_vulnerability_poc_flow(management, collector):
    """ Test that vulnerable app version in communication control get vulnerability from FCS.
     Because it is part of POC flow this test is GUI oriented.
     1. Install a vulnerable version like firefox 68
     2. Wait until it appear in the communication control apps.
     3. Validate that the vulnerability is 'UNKNOWN'.
     4. Wait until FCS will determine the correct vulnerability ('Critical').
     5. Uninstall the app and delete from management comm control apps list.
    """
    assert isinstance(collector, WindowsCollector), "Support only a windows collector"
    assert management.is_connected_to_fcs(), \
        f"{management} is not connected to FCS, status is: {management.get_fcs_status()}"
    tenant = management.tenant
    collector_agent = collector
    user = tenant.default_local_admin
    vulnerable_app_name = AppsNames.FIREFOX.value

    Reporter.report(f"Setup - set communication control vulnerable firefox env testing for {collector_agent}", INFO)
    with setup_vulnerable_app_firefox_env_context(collector_agent, management):

        with TEST_STEP(f"STEP- Check that vulnerable app {vulnerable_app_name} appears in Communication Control apps"):
            CommControlAppUtils.wait_until_app_cluster_appear_in_comm_control_apps(app_name=vulnerable_app_name,
                                                                                   tenant=tenant)
        with TEST_STEP(f"STEP- Check that app {vulnerable_app_name} still didn't get vulnerability category"):
            comm_control_app_cluster = user.rest_components.comm_control_app.get_app_installed_versions_cluster_by_name(
                app_name=vulnerable_app_name, safe=False)
            not_vulnarable = AppsVulnerabilities.UNKNOWN.value
            actual_vulnerability = comm_control_app_cluster.get_severity()
            assert actual_vulnerability.lower() == not_vulnarable.lower(), \
                f"Actual vulnerability: {actual_vulnerability}, expected: {not_vulnarable}"

        with TEST_STEP(f"STEP- Wait until app {vulnerable_app_name} will get vulnerability category in GUI"):
            critical = AppsVulnerabilities.CRITICAL.value
            CommControlAppUtils.wait_for_app_vulnerability(management=management, app_name=vulnerable_app_name,
                                                           vulnerability=critical)
            CommControlAppUtils.validate_app_vulnerability_via_gui(management=management, app_name=vulnerable_app_name,
                                                                   vulnerability=critical)


@allure.epic("POC FLOW")
@allure.feature("Communication control")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.poc_flow
@pytest.mark.fcs_sanity
@pytest.mark.security_policies
@pytest.mark.security_policies_sanity
@pytest.mark.xray('EN-78749')
def test_malware_is_blocked_poc_flow(fx_system_without_events_and_exceptions, collector):
    """ Test that malware is blocked. Because it is part of POC flow this test is GUI oriented. """
    management = fx_system_without_events_and_exceptions
    assert isinstance(collector, WindowsCollector), "Support only a windows collector"

    rule_name = RulesNames.MALICIOUS_FILE_DETECTED.value
    policy_name = DefaultPoliciesNames.EXECUTION_PREVENTION.value
    malware_name = get_relevant_malware_name(policy_name=policy_name, rule_name=rule_name)
    tenant = management.tenant
    user = tenant.default_local_admin
    policy = user.rest_components.security_policies.get_by_name(policy_name=policy_name)
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    Reporter.report(f"Prepare env for testing security policy UI {policy_name}", INFO)

    with _setup_env_for_gui_test_security_policy_context(windows_collector=collector, management=management,
                                                         policy=policy):
        Reporter.report(f"Set {policy_name} to simulation mode because later we want to set it to prevention mode "
                        f"via UI and validate that prevention is turned on in UI", INFO)
        with wait_till_configuration_drill_down_to_collector(collector_agent=collector):
            policy.set_policy_mode(mode_name=ModeNames.SIMULATION.value, safe=True)

        with TEST_STEP(f"STEP-Set {policy_name} to prevention mode via UI and validate prevention turned on in UI"):
            with wait_till_configuration_drill_down_to_collector(collector_agent=collector):
                set_policy_mode_ui(policy_name=policy_name, mode_name=ModeNames.PREVENTION.value,
                                   management=management)

        with TEST_STEP(f"STEP- Validate rule '{rule_name}' is enabled and the action is set to block"):
            rule_action = policy.get_rule_action(rule_name=rule_name)
            assert rule_action == RuleActions.BLOCK.value, f"Rule {rule_name} action is wrong: {rule_action}"
            rule_state = policy.get_rule_state(rule_name=rule_name)
            assert rule_state == RuleStates.ENABLED.value, f"Rule {rule_name} state is wrong: {rule_state}"

        with TEST_STEP(f"STEP-Trigger a malicious {malware_name} in order to create event for the tested policy"):
            collector.create_event(malware_name=malware_name)

        with TEST_STEP("STEP-wait for event and validate that event created with the correct values in UI"):
            validate_event_ui(malware_name=malware_name, is_blocked=True,
                              collector_name=rest_collector.get_name(), management=management)
            events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True,
                                                                     wait_for=True)
            event = events[0]
            rules = event.get_rules()
            assert len(rules) == 1, f"Event should have only this rule {rule_name} but got these rules: {rules}"
            assert rules[0] == rule_name, f"Event is triggered by this rule: {rules[0]} instead of rule '{rule_name}'"


@contextmanager
def _setup_env_for_gui_test_security_policy_context(windows_collector: WindowsCollector, management: Management,
                                                    policy: SecurityPolicy):
    assert isinstance(windows_collector, WindowsCollector), "Support only a windows collector"
    tenant = management.tenant
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=windows_collector.host_ip)
    policy_name = policy.name
    user = tenant.default_local_admin

    with TEST_STEP(f"Setup - Prepare env for testing security policy UI"):
        Reporter.report(f"Validate that {windows_collector} is in the default group", INFO)
        assert rest_collector.get_group_name() == DEFAULT_COLLECTOR_GROUP_NAME, \
            f"Bug in test setup - The collector is not in the default group '{DEFAULT_COLLECTOR_GROUP_NAME}'"
        Reporter.report(f"Validate that default collector group is assigned to {policy}", INFO)
        assert policy.is_default_group_assigned(), \
            f"ERROR - Policy '{policy_name}' is not assigned to 'Default Collector Group'"

    Reporter.report(f"Set {policy_name} to simulation mode because later we want to set it to prevention mode "
                    f"via UI and validate that prevention is turned on in UI", INFO)
    with change_policy_mode_context(user=user, policy_name=policy_name):
        yield
