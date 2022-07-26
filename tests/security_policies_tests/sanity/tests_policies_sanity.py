import logging

import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.api.management_api.event import EventActionNames
from infra.api.management_api.policy import DefaultPoliciesNames, RulesNames
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from tests.utils.policy_utils import disable_rule_in_policies_context, \
    change_policy_rule_fields_context, change_policy_mode_context, get_relevant_malware_name

logger = logging.getLogger(__name__)


_RULE_NAME_BY_TESTED_POLICY = {
    DefaultPoliciesNames.EXECUTION_PREVENTION.value: RulesNames.MALICIOUS_FILE_DETECTED.value,
    DefaultPoliciesNames.EXFILTRATION_PREVENTION.value: RulesNames.STACK_PIVOT.value,
    DefaultPoliciesNames.RANSOMWARE_PREVENTION.value: RulesNames.DYNAMIC_CODE.value
}


def _get_rule_name_by_policy_name(policy_name):
    return _RULE_NAME_BY_TESTED_POLICY[policy_name]


@allure.epic("Management")
@allure.feature("Policy")
@pytest.mark.policy
@pytest.mark.sanity
@pytest.mark.policy_sanity
@pytest.mark.management_sanity
@pytest.mark.parametrize(
    "xray, policy_name",
    [('EN-78065', DefaultPoliciesNames.EXECUTION_PREVENTION.value),
     ('EN-78300', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value),
     ('EN-78302', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value)
     ],
)
def test_policy_simulation_mode_windows(fx_system_without_events_and_exceptions, collector, xray, policy_name):
    """
        Test that policy in simulation mode catching relevant malware and creating correct security event

            1. Start the test on clean system: without exceptions and without events
            2. disable rule in all policies except the tested policy because we trigger malware (from collector)
               that should be caught by the tested policy and not to other policy
            3. Change policy's rule , the action to block and the state to enabled because
               we trigger malware (from collector) that should be caught by the tested policy in action simulation
               and for this action the policy's rule must be in block action and enabled state
            4. Assign policy to collector group and set to simulation mode
            5. Trigger malware (from collector) that should be caught by the tested policy
            6. Validate that event created by the tested policy and by the simulation mode
    """
    assert isinstance(collector, WindowsCollector), "This test trigger malware only on a windows collector"
    rule_name = _get_rule_name_by_policy_name(policy_name=policy_name)
    malware_name = get_relevant_malware_name(policy_name=policy_name, rule_name=rule_name)
    management = fx_system_without_events_and_exceptions
    collector_agent = collector
    rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    user = management.tenant.default_local_admin
    all_policies = user.rest_components.policies.get_all()
    not_tested_policies_names = [policy.name for policy in all_policies if policy.name != policy_name]
    policy = [policy for policy in all_policies if policy.name == policy_name][0]
    group = user.rest_components.collector_groups.get_by_name(name=rest_collector.get_group_name())

    with TEST_STEP(f"Assign {policy} to {group}"):
        policy.assign_to_collector_group(group_name=group.name, safe=True)

    logger.info(f"Disable rule '{rule_name}' in policies {not_tested_policies_names} in order to isolate our rule")
    with disable_rule_in_policies_context(user=user, policies_names=not_tested_policies_names, rule_name=rule_name):
        with change_policy_mode_context(user=user, policy_name=policy_name):
            with change_policy_rule_fields_context(user=user, policy_name=policy_name, rule_name=rule_name):
                with TEST_STEP(f"Change {policy_name}'s rule '{rule_name}', the action to block and the state to enabled"):
                    policy.set_rule_action_to_block(rule_name=rule_name, safe=True)
                    policy.set_rule_state_to_enabled(rule_name=rule_name, safe=True)

                with TEST_STEP(f"Set mode of {policy_name} policy to simulation mode"):
                    policy.set_to_simulation_mode(safe=True)

                with TEST_STEP(f"Trigger a malicious {malware_name} in order to create event for the tested policy"):
                    collector.create_event(malware_name=malware_name)

                with TEST_STEP(f"Validate created right event by malware-{malware_name} in mode simulation"):
                    events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True
                                                                             , wait_for=True)
                    event = events[0]
                    assert len(events) == 1, f"ERROR - Created {len(events)} events, expected of 1"
                    assert rule_name in event.get_rules(), f"ERROR - The event is not connected to our policy"
                    assert event.get_process_name() == malware_name, f"ERROR - Created event by process " \
                                                                     f"{event.get_process_name()}, " \
                                                                     f"expected by process {malware_name}"
                    assert event.get_action() == EventActionNames.SIMULATION_BLOCK.value,\
                        f"ERROR - Created event in {event.get_action()} action, expected" \
                        f" {EventActionNames.SIMULATION_BLOCK.value} action"











