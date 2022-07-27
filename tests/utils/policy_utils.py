import logging
from contextlib import contextmanager

import allure

from infra.api.management_api.policy import DefaultPoliciesNames, RulesNames, set_policies_rule_state_to_disabled, \
     set_policies_rules_states
from infra.api.management_api.user import User
from typing import List
from enum import Enum

logger = logging.getLogger(__name__)


class WindowsMalwaresNames(Enum):
    EVIL_PROCESS_LAUNCHER = 'EvilProcessLauncherTests.exe'
    STACK_PIVOT = 'StackPivotTests.exe'
    USER_HEAP = 'UserHeapTests.exe'


MALWARE_NAME_MAP_PER_RULE_NAME = {
    DefaultPoliciesNames.EXECUTION_PREVENTION.value:
        {RulesNames.MALICIOUS_FILE_DETECTED.value: WindowsMalwaresNames.EVIL_PROCESS_LAUNCHER.value},
    DefaultPoliciesNames.EXFILTRATION_PREVENTION.value:
        {RulesNames.STACK_PIVOT.value: WindowsMalwaresNames.STACK_PIVOT.value},
    DefaultPoliciesNames.RANSOMWARE_PREVENTION.value:
        {RulesNames.DYNAMIC_CODE.value: WindowsMalwaresNames.USER_HEAP.value}
}


def get_relevant_malware_name(policy_name, rule_name):
    """ Find the malware that will trigger event for the given rule of the given policy"""
    return MALWARE_NAME_MAP_PER_RULE_NAME[policy_name][rule_name]


@contextmanager
def change_policy_rule_fields_context(user: User, policy_name, rule_name):
    """
       Change policy rule's fields:state, action and finally return to previous rule's fields
    """
    policy = user.rest_components.policies.get_by_name(policy_name=policy_name)
    old_state = policy.get_rule_state(rule_name=rule_name)
    old_action = policy.get_rule_action(rule_name=rule_name)
    try:
        yield
    finally:
        with allure.step(f"Cleanup - return the rule '{rule_name}' fields to the original values,policy {policy_name}"):
            policy.set_rule_action(rule_name=rule_name, action=old_action, safe=True)
            policy.set_rule_state(rule_name=rule_name, state=old_state, safe=True)


@contextmanager
def change_policy_mode_context(user: User, policy_name):
    policy = user.rest_components.policies.get_by_name(policy_name=policy_name)
    old_mode = policy.get_operation_mode()
    try:
        yield
    finally:
        with allure.step(f"Cleanup - return policy '{policy_name}' to the original mode {old_mode}"):
            policy.set_policy_mode(mode_name=old_mode, safe=True)


@contextmanager
def disable_rule_in_policies_context(user: User, policies_names: List[str], rule_name):
    """
        Disable the rule in the all given policies and finally return to previous rule state
    """
    with allure.step(f"Setup- Disable the rule '{rule_name}' in these policies: {policies_names}"):
        policies = []
        original_rule_state_by_policy_name = {}
        for policy_name in policies_names:
            policy = user.rest_components.policies.get_by_name(policy_name=policy_name)
            if policy.get_rule_by_name(rule_name=rule_name, safe=True) is not None:
                original_rule_state_by_policy_name[policy_name] = policy.get_rule_state(rule_name=rule_name)
                policies.append(policy)
        set_policies_rule_state_to_disabled(policies=policies, rule_name=rule_name)
    try:
        yield
    finally:
        with allure.step("Cleanup - for each policy return the given rule to the original state"):
            policies_rules_original_states = []
            for policy in policies:
                policy_rule_original_state = (policy, rule_name, original_rule_state_by_policy_name[policy.name])
                policies_rules_original_states.append(policy_rule_original_state)
            set_policies_rules_states(policies_rules_states=policies_rules_original_states)

