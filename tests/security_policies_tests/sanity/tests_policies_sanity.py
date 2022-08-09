import logging

import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.api.management_api.event import EventActionNames
from infra.api.management_api.policy import DefaultPoliciesNames, RulesNames, ModeNames
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
    "xray, policy_name, mode",
    [('EN-78065', DefaultPoliciesNames.EXECUTION_PREVENTION.value, ModeNames.SIMULATION.value),
     ('EN-78300', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.SIMULATION.value),
     ('EN-78302', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value, ModeNames.SIMULATION.value),
     ('EN-78352', DefaultPoliciesNames.EXECUTION_PREVENTION.value, ModeNames.PREVENTION.value),
     ('EN-78361', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value, ModeNames.PREVENTION.value),
     ('EN-78359', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.PREVENTION.value)
     ],
)
def test_policy_mode_on_windows_os(fx_system_without_events_and_exceptions, collector, xray, policy_name, mode):
    """
        Test that policy modes simulation/prevention catching relevant malware and creating correct security event with
        block action

            1. Start the test on clean system: without exceptions and without events
            2. disable rule in all policies except the tested policy because we trigger malware (from collector)
               that should be caught by the tested policy and not to other policy
            3. Enable policy rule and validate that the rule is on 'block' because
               we trigger malware (from collector) that should be caught by the tested policy in our mode
               and for this mode the policy's rule must be in block action and enabled state
            4. Assign policy to collector group and set to simulation/prevention mode
            5. Trigger malware (from collector) that should be caught by the tested policy
            6. Validate that event created with the correct fields
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

    with TEST_STEP(f"STEP-Assign policy '{policy_name}' to {group}"):
        policy.assign_to_collector_group(group_name=group.name, safe=True)

    logger.info(f"Disable rule '{rule_name}' in policies {not_tested_policies_names} in order to isolate our rule")
    with disable_rule_in_policies_context(user=user, policies_names=not_tested_policies_names, rule_name=rule_name):
        with change_policy_mode_context(user=user, policy_name=policy_name):
            with change_policy_rule_fields_context(user=user, policy_name=policy_name, rule_name=rule_name):
                with TEST_STEP(f"STEP-Enable the rule '{rule_name}' and set action to the 'block' action"):
                    policy.set_rule_action_to_block(rule_name=rule_name, safe=True)
                    policy.set_rule_state_to_enabled(rule_name=rule_name, safe=True)

                with TEST_STEP(f"STEP-Set mode of policy '{policy_name}' to '{mode}' mode"):
                    policy.set_policy_mode(mode_name=mode, safe=True)

                with TEST_STEP(f"STEP-Trigger a malicious {malware_name} in order to create event for the tested policy"):
                    collector.create_event(malware_name=malware_name)

                with TEST_STEP("STEP-Validate that event created with the correct values"):
                    events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True
                                                                             , wait_for=True)
                    assert len(events) == 1, f"ERROR - Created {len(events)} events, expected of 1"
                    event = events[0]
                    assert rule_name in event.get_rules(), f"ERROR - The event is not connected to our policy"
                    assert event.get_process_name() == malware_name, f"ERROR - Created event by process " \
                                                                     f"{event.get_process_name()}, " \
                                                                     f"expected by process {malware_name}"
                    expected_action = EventActionNames.SIMULATION_BLOCK.value if mode == ModeNames.SIMULATION.value \
                        else EventActionNames.BLOCK.value
                    assert event.get_action() == expected_action,\
                           f"ERROR - Created event in {event.get_action()} action, expected" \
                           f" {expected_action} action"


@allure.epic("Management")
@allure.feature("Policy")
@pytest.mark.policy
@pytest.mark.sanity
@pytest.mark.policy_sanity
@pytest.mark.management_sanity
@pytest.mark.parametrize(
    "xray, policy_name",
    [('EN-78675', DefaultPoliciesNames.EXECUTION_PREVENTION.value),
     ('EN-78676', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value),
     ('EN-78677', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value),
     ('EN-78678', DefaultPoliciesNames.DEVICE_CONTROL.value),
     ('EN-78679', DefaultPoliciesNames.EXTENDED_DETECTION.value)
     ],)
def test_delete_main_policy(management, xray, policy_name):
    """
        Test that can not delete main policy
        Test steps:
        1. Select Execution Prevention policy, Delete the policy, validate can not delete.
        2. Validate that the  policy is exists
    """
    user = management.tenant.default_local_admin
    with TEST_STEP(f"Select the policy '{policy_name}', Delete the policy, validate can not delete"):
        test_im_params = {
            "loginUser": management.tenant.default_local_admin.get_username(),
            "loginPassword": management.tenant.default_local_admin.password,
            "loginOrganization": management.tenant.default_local_admin.password,
            "organization": management.tenant.organization.get_name(),
            "policyName": policy_name
        }
        logger.info(f"Try to delete the policy '{policy_name}', validate can not delete")
        management.ui_client.security_policies.validate_cannot_delete_default_policies(data=test_im_params)

    with TEST_STEP(f"Validate that the policy '{policy_name}' is exists"):
        user.rest_components.policies.get_by_name(policy_name=policy_name)










