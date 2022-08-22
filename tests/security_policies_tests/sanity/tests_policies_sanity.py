import logging

import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter, INFO
from infra.api.management_api.event import EventActionNames
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.api.management_api.policy import DefaultPoliciesNames, RulesNames, ModeNames, RuleActions, \
    ExternalPoliciesNames
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from sut_details import collector_type
from tests.utils.collector_group_utils import new_group_with_collector_context
from tests.utils.policy_utils import change_policy_rule_fields_context, change_policy_mode_context, \
    get_relevant_malware_name

logger = logging.getLogger(__name__)


_WINDOWS_RULE_NAME_BY_TESTED_POLICY = {
    DefaultPoliciesNames.EXECUTION_PREVENTION.value: RulesNames.MALICIOUS_FILE_DETECTED.value,
    DefaultPoliciesNames.EXFILTRATION_PREVENTION.value: RulesNames.STACK_PIVOT.value,
    DefaultPoliciesNames.RANSOMWARE_PREVENTION.value: RulesNames.DYNAMIC_CODE.value
}

_LINUX_RULE_NAME_BY_TESTED_POLICY = {
    DefaultPoliciesNames.EXFILTRATION_PREVENTION.value: RulesNames.UNCONFIRMED_EXECUTABLE.value
}


def _get_rule_name_by_policy_name(collector_agent: CollectorAgent, policy_name):
    if isinstance(collector_agent, WindowsCollector):
        return _WINDOWS_RULE_NAME_BY_TESTED_POLICY[policy_name]
    elif isinstance(collector_agent, LinuxCollector):
        return _LINUX_RULE_NAME_BY_TESTED_POLICY[policy_name]
    else:
        assert False, f"ERROR - Not supported {collector_type}!!!"


def _generate_params_for_test_policy_mode_with_rule_block():
    linux = [('EN-78981', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.SIMULATION.value),
             ('EN-78982', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.PREVENTION.value)]
    windows = [('EN-78065', DefaultPoliciesNames.EXECUTION_PREVENTION.value, ModeNames.SIMULATION.value),
               ('EN-78300', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.SIMULATION.value),
               ('EN-78302', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value, ModeNames.SIMULATION.value),
               ('EN-78352', DefaultPoliciesNames.EXECUTION_PREVENTION.value, ModeNames.PREVENTION.value),
               ('EN-78361', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value, ModeNames.PREVENTION.value),
               ('EN-78359', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value, ModeNames.PREVENTION.value)]
    if 'linux' in collector_type.lower():
        return linux
    elif 'windows' in collector_type.lower():
        return windows
    else:
        assert False, f"ERROR - Not supported {collector_type}!!!"


params_for_test_policy_mode_with_rule_block = _generate_params_for_test_policy_mode_with_rule_block()


@allure.epic("Management")
@allure.feature("Policy")
@pytest.mark.policy
@pytest.mark.sanity
@pytest.mark.policy_sanity
@pytest.mark.management_sanity
@pytest.mark.parametrize(
    "xray, policy_name, mode",
    params_for_test_policy_mode_with_rule_block,
)
def test_policy_mode_with_rule_block(fx_system_without_events_and_exceptions, collector, xray, policy_name, mode):
    """
        Test that policy modes simulation/prevention catching relevant malware and creating correct security event with
        block action and is(in prevention mode)/isn't(in simulation mode) blocked the malware on collector agent

            1. Start the test on clean system: without exceptions and without events
            2. Assign policy to new collector group
            3. Enable policy rule and validate that the rule is on 'block' because
               we trigger malware (from collector) that should be caught by the tested policy in our mode
               and for this mode the policy's rule must be in block action and enabled state
            4. Set to simulation/prevention mode
            5. Trigger malware (from collector) that should be caught by the tested policy
            6. Validate that event created with the correct fields
            7. TODO: Validate that the malware is(in prevention mode)/isn't(in simulation mode) blocked on collector agent
    """
    rule_name = _get_rule_name_by_policy_name(collector_agent=collector, policy_name=policy_name)
    malware_name = get_relevant_malware_name(policy_name=policy_name, rule_name=rule_name)
    management = fx_system_without_events_and_exceptions
    user = management.tenant.default_local_admin
    policy = user.rest_components.policies.get_by_name(policy_name=policy_name)

    with new_group_with_collector_context(management=management,
                                          collector_agent=collector) as group_with_collector:
        target_group_name, target_collector = group_with_collector
        with TEST_STEP(f"STEP-Assign policy '{policy_name}' to new group '{target_group_name}'"):
            policy.assign_to_collector_group(group_name=target_group_name, safe=True)

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
                    assert len(event.get_rules()) == 1 and rule_name in event.get_rules(),\
                        f"ERROR -The event was not triggered by the correct rule"
                    assert event.get_process_name() == malware_name, f"ERROR - Created event by process " \
                                                                     f"{event.get_process_name()}, " \
                                                                     f"expected by process {malware_name}"
                    expected_action = EventActionNames.SIMULATION_BLOCK.value if mode == ModeNames.SIMULATION.value \
                        else EventActionNames.BLOCK.value
                    assert event.get_action() == expected_action,\
                           f"ERROR - Created event in {event.get_action()} action, expected" \
                           f" {expected_action} action"

                    with TEST_STEP(f"STEP-Validate that the malicious '{malware_name}' is {expected_action} on {collector}"):
                        pass


def _generate_params_for_test_policy_rule_action_log():
    linux = [('EN-79033', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value)]
    windows = [('EN-78442', DefaultPoliciesNames.EXECUTION_PREVENTION.value),
               ('EN-78446', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value),
               ('EN-78448', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value)]
    if 'linux' in collector_type.lower():
        return linux
    elif 'windows' in collector_type.lower():
        return windows
    else:
        assert False, f"ERROR - Not supported {collector_type}!!!"


params_for_test_policy_rule_action_log = _generate_params_for_test_policy_rule_action_log()


@allure.epic("Management")
@allure.feature("Policy")
@pytest.mark.policy
@pytest.mark.sanity
@pytest.mark.policy_sanity
@pytest.mark.management_sanity
@pytest.mark.parametrize(
    "xray, policy_name",
    params_for_test_policy_rule_action_log
    ,)
def test_policy_rule_action_log(fx_system_without_events_and_exceptions, collector, xray, policy_name):
    """
        Test that policy rule in action 'Log', catching relevant malware and creating correct security event
        and is not blocked the malware on collector agent
        *** The block action is already tested in test 'test_policy_mode_with_rule_block' ***

            1. Start the test on clean system: without exceptions and without events
            2. Assign policy to new collector group
            3. Set the policy to prevention mode and Enable policy rule because we trigger malware (from collector) that
               should be caught by the tested policy in 'Log' action and for the that
               policy must be in prevention mode and rule in enabled state
            4. Set the rule action to the 'Log' action
            5. Trigger malware (from collector) that should be caught by the tested policy
            6. Validate that event created with the correct fields
            7. TODO: Validate that the malware is not blocked on collector agent
    """
    rule_name = _get_rule_name_by_policy_name(collector_agent=collector, policy_name=policy_name)
    malware_name = get_relevant_malware_name(policy_name=policy_name, rule_name=rule_name)
    management = fx_system_without_events_and_exceptions
    user = management.tenant.default_local_admin
    policy = user.rest_components.policies.get_by_name(policy_name=policy_name)

    with new_group_with_collector_context(management=management,
                                          collector_agent=collector) as group_with_collector:
        target_group_name, target_collector = group_with_collector

        with TEST_STEP(f"STEP-Assign policy '{policy_name}' to new group '{target_group_name}'"):
            policy.assign_to_collector_group(group_name=target_group_name, safe=True)

        with change_policy_mode_context(user=user, policy_name=policy_name):
            with change_policy_rule_fields_context(user=user, policy_name=policy_name, rule_name=rule_name):
                with TEST_STEP(f"STEP--Set mode of policy '{policy_name}' to 'prevention' mode and "
                               f"Enable the rule '{rule_name}'"):
                    policy.set_rule_state_to_enabled(rule_name=rule_name, safe=True)
                    policy.set_to_prevention_mode(safe=True)

                with TEST_STEP(f"STEP- Set the rule '{rule_name}' action to the 'Log' action"):
                    policy.set_rule_action_to_log(rule_name=rule_name, safe=True)

                with TEST_STEP(f"STEP-Trigger a malicious {malware_name} in order to create event for the tested policy"):
                    collector.create_event(malware_name=malware_name)

                with TEST_STEP("STEP-Validate that event created with the correct values"):
                    events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True,
                                                                             wait_for=True)
                    assert len(events) == 1, f"ERROR - Created {len(events)} events, expected of 1"
                    event = events[0]
                    assert len(event.get_rules()) == 1 and rule_name in event.get_rules(), \
                        f"ERROR -The event was not triggered by the correct rule"
                    assert event.get_process_name() == malware_name, f"ERROR - Created event by process " \
                                                                     f"{event.get_process_name()}, " \
                                                                     f"expected by process {malware_name}"
                    assert event.get_action() == RuleActions.LOG.value,\
                           f"ERROR - Created event in {event.get_action()} action, expected" \
                           f" {RuleActions.LOG.value} action"

                with TEST_STEP(f"STEP-Validate that the malicious '{malware_name}' is not blocked on {collector}"):
                    pass


def _generate_params_for_test_disabled_policy_rule_state():
    linux = [('EN-79034', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value)]
    windows = [('EN-78443', DefaultPoliciesNames.EXECUTION_PREVENTION.value),
               ('EN-78447', DefaultPoliciesNames.EXFILTRATION_PREVENTION.value),
               ('EN-78454', DefaultPoliciesNames.RANSOMWARE_PREVENTION.value)]
    if 'linux' in collector_type.lower():
        return linux
    elif 'windows' in collector_type.lower():
        return windows
    else:
        assert False, f"ERROR - Not supported {collector_type}!!!"


params_for_test_disabled_policy_rule_state = _generate_params_for_test_disabled_policy_rule_state()


@allure.epic("Management")
@allure.feature("Policy")
@pytest.mark.policy
@pytest.mark.sanity
@pytest.mark.policy_sanity
@pytest.mark.management_sanity
@pytest.mark.parametrize(
    "xray, policy_name",
    params_for_test_disabled_policy_rule_state,
)
def test_disabled_policy_rule_state(fx_system_without_events_and_exceptions, collector, xray, policy_name):
    """
        Test that a disabled rule is not blocking the malware on the collector agent and is not creating new event
        ***
        The enable mode is already tested in tests:
            - test_policy_mode_with_rule_block
            - test_policy_rule_action_log
        ***
            1. Start the test on clean system: without exceptions and without events
            2. Assign policy to new collector group
            3. Set the policy to prevention mode and validate that the rule is on 'block'
               because we trigger malware (from collector) that should be caught by the tested policy in 'Disabled' state
               and for that the policy must be on prevention mode and the rule must be in block action
            4. Set the rule state to the 'disabled' state
            5. Trigger malware (from collector) that should be caught by the tested policy
            6. Validate that not created any event
    """
    rule_name = _get_rule_name_by_policy_name(collector_agent=collector, policy_name=policy_name)
    malware_name = get_relevant_malware_name(policy_name=policy_name, rule_name=rule_name)
    management = fx_system_without_events_and_exceptions
    user = management.tenant.default_local_admin
    policy = user.rest_components.policies.get_by_name(policy_name=policy_name)

    with new_group_with_collector_context(management=management,
                                          collector_agent=collector) as group_with_collector:
        target_group_name, target_collector = group_with_collector

        with TEST_STEP(f"STEP-Assign policy '{policy_name}' to new group '{target_group_name}'"):
            policy.assign_to_collector_group(group_name=target_group_name, safe=True)

        with change_policy_mode_context(user=user, policy_name=policy_name):
            with change_policy_rule_fields_context(user=user, policy_name=policy_name, rule_name=rule_name):
                with TEST_STEP(f"STEP-Set mode of policy '{policy_name}' to 'prevention' mode and "
                               f"rule '{rule_name}' action to the 'block' action"):
                    policy.set_to_prevention_mode(safe=True)
                    policy.set_rule_action_to_block(rule_name=rule_name, safe=True)

                with TEST_STEP(f"STEP-Set the rule '{rule_name}' state to the 'disabled' state"):
                    policy.set_rule_state_to_disabled(rule_name=rule_name, safe=True)

                with TEST_STEP(f"STEP-Trigger a malicious {malware_name} in order to create event for the tested policy"):
                    collector.create_event(malware_name=malware_name)

                with TEST_STEP("STEP-Validate that not created any event"):
                    events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True,
                                                                             wait_for=True)
                    assert len(events) == 0, f"ERROR - Created {len(events)} events, expected of 0"

                with TEST_STEP(f"STEP-Validate that the malicious '{malware_name}' is not blocked on {collector}"):
                    pass


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
     ('EN-78678', ExternalPoliciesNames.DEVICE_CONTROL.value),
     ('EN-78679', ExternalPoliciesNames.EXTENDED_DETECTION.value)
     ],)
def test_can_not_delete_main_policy(management, xray, policy_name):
    """
        Test that can not delete main policy

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









