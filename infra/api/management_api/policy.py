import logging
from typing import List
import allure
import time
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.common_utils import WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
logger = logging.getLogger(__name__)


WAIT_AFTER_ASSIGN = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
WAIT_AFTER_SET_POLICY_MODE = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
WAIT_AFTER_SET_RULE_ACTION_STATE = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION


class PolicyFieldsNames(Enum):
    """ Policy's fields names as we get from server """
    NAME = 'name'
    ORGANIZATION = 'organization'
    OPERATION_MODE = 'operationMode'
    COLLECTORS_GROUPS = 'agentGroups'
    RULES = 'rules'


class RuleFieldsNames(Enum):
    """ Rule's fields names as we get from server """
    NAME = 'name'
    SHORT_NAME = 'shortName'
    STATE = 'enabled'
    ACTION = 'securityAction'


class DefaultPoliciesNames(Enum):
    EXECUTION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXECUTION_PREVENTION
    EXFILTRATION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION
    RANSOMWARE_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION
    DEVICE_CONTROL = 'Device Control'
    EXTENDED_DETECTION = 'eXtended Detection'


class RulesNames(Enum):
    MALICIOUS_FILE_DETECTED = 'Malicious File Detected'
    STACK_PIVOT = 'Stack Pivot'
    DYNAMIC_CODE = 'Dynamic Code'


class ModeNames(Enum):
    PREVENTION = NsloRest.NSLO_PREVENTION_MODE
    SIMULATION = NsloRest.NSLO_SIMULATION_MODE


class RuleStates(Enum):
    ENABLED = NsloRest.NSLO_ENABLED_MODE
    DISABLED = NsloRest.NSLO_DISABLED_MODE


class RuleActions(Enum):
    BLOCK = 'Block'
    LOG = 'Log'


class Policy(BaseApiObj):
    """ A wrapper of our internal rest client for working with policies.
        Each policy will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._name = initial_data[PolicyFieldsNames.NAME.value]  # Static, unique identifier

    def __repr__(self):
        return f"Policy {self.name} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def name(self) -> str:
        return self._name

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = PolicyFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_operation_mode(self, from_cache=None, update_cache=True):
        field_name = PolicyFieldsNames.OPERATION_MODE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_collector_groups(self, from_cache=None, update_cache=True) -> List[str]:
        field_name = PolicyFieldsNames.COLLECTORS_GROUPS.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_rules(self, from_cache=None, update_cache=True) -> List[dict]:
        field_name = PolicyFieldsNames.RULES.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_rule_by_name(self, rule_name, safe=False, from_cache=None, update_cache=True) -> dict:
        rules = [rule for rule in self.get_rules(from_cache=from_cache, update_cache=update_cache)
                 if rule[RuleFieldsNames.SHORT_NAME.value] == rule_name]
        if len(rules) == 1:
            logger.debug(f"Found this rule: \n {rules}")
            return rules[0]
        assert len(rules) < 2, f"Found bug, there are {len(rules)} rules with the same name {rule_name}"
        assert safe, f"Didn't find  rule {rule_name}  in policy {self.name}"
        logger.info(f"Didn't find rule {rule_name} in policy {self.name}")
        return None

    def get_rule_action(self, rule_name) -> str:
        rule = self.get_rule_by_name(rule_name=rule_name)
        return rule[RuleFieldsNames.ACTION.value]

    def get_rule_state(self, rule_name) -> str:
        rule = self.get_rule_by_name(rule_name=rule_name)
        if rule[RuleFieldsNames.STATE.value].lower() == 'true':
            return RuleStates.ENABLED.value
        else:
            return RuleStates.DISABLED.value

    def is_group_assigned(self, group_name) -> bool:
        assigned_groups_names = self.get_collector_groups()
        return group_name in assigned_groups_names

    def _get_field(self, field_name, from_cache, update_cache):
        from_cache = from_cache if from_cache is not None else self._use_cache
        if from_cache:
            value = self._cache[field_name]
        else:
            updated_value = self.get_fields()[field_name]
            value = updated_value
            if update_cache:
                self._cache[field_name] = updated_value
        return value

    def create(self):
        raise NotImplemented("Policy can't be created")

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        policies_fields = rest_client.policies.get_policies()
        for policy_fields in policies_fields:
            if policy_fields[PolicyFieldsNames.NAME.value] == self.name:
                logger.debug(f"{self} updated data from management: \n {policy_fields}")
                if update_cache_data:
                    self.cache = policy_fields
                return policy_fields
        assert safe, f"Policy with name {self.name} was not found"
        logger.debug(f"Policy with name {self.name} was not found")
        return None

    @allure.step("Delete Policy")
    def delete(self):
        """ Delete policy from management using user credentials """
        self._delete()

    def _delete(self, expected_status_code=200):
        raise NotImplemented("Should be implemented, check which credentials are required")

    def update_fields(self, safe=False):
        raise NotImplemented("Not relevant")

    @allure.step("Assign this policy to collector group")
    def assign_to_collector_group(self, group_name, wait_sec=None, safe=False):
        logger.info(f"Assign {self} to the collector group {group_name}")
        self.assign_to_collector_groups(groups_names=[group_name], wait_sec=wait_sec, safe=safe)

    @allure.step("Assign this policy to collector groups")
    def assign_to_collector_groups(self, groups_names: list, wait_sec=None, safe=False):
        group_names_to_assign = []
        wait_sec = wait_sec or WAIT_AFTER_ASSIGN
        assigned_collector_groups = self.get_collector_groups()
        for group_name in groups_names:
            is_assigned = True if group_name in assigned_collector_groups else False
            if is_assigned:
                assert safe, f"{group_name} already assigned to {self}!"
                logger.info(f"{group_name} already assigned to {self}!")
                continue
            else:
                group_names_to_assign.append(group_name)
        logger.info(f"Assign {self} to these collector groups {group_names_to_assign}")
        if len(group_names_to_assign):
            self._rest_client.policies.assign_policy(policy_name=self.name, group_name=group_names_to_assign)
            logger.info(f"Sleep {wait_sec} seconds after assigning policy")
            time.sleep(wait_sec)

    @allure.step("Set policy to prevention mode")
    def set_to_prevention_mode(self, wait=True, safe=False):
        self.set_policy_mode(mode_name=ModeNames.PREVENTION.value, wait=wait, safe=safe)

    @allure.step("Set policy to simulation mode")
    def set_to_simulation_mode(self, wait=True, safe=False):
        self.set_policy_mode(mode_name=ModeNames.SIMULATION.value, wait=wait, safe=safe)

    @allure.step("Set policy mode")
    def set_policy_mode(self, mode_name, wait=True, safe=False, wait_sec=None):
        is_in_expected_mode = True if self.get_operation_mode() == mode_name else False
        wait_sec = wait_sec or WAIT_AFTER_SET_POLICY_MODE
        if is_in_expected_mode:
            assert safe, f"{self} already in {mode_name} mode!"
            logger.info(f"{self} already in {mode_name} mode!")
        else:
            logger.info(f"Set {self} mode to {mode_name}")
            self._rest_client.policies.set_policy_mode(name=self.name, mode=mode_name)
            if wait:
                logger.info(f"Sleep {wait_sec} seconds after set policy mode to {mode_name}")
                time.sleep(wait_sec)

    @allure.step("Set policy rule state to enabled")
    def set_rule_state_to_enabled(self, rule_name, wait=True, safe=False):
        self.set_rule_state(rule_name=rule_name, state=RuleStates.ENABLED.value,
                            wait=wait, safe=safe)

    @allure.step("Set policy rule state to disabled")
    def set_rule_state_to_disabled(self, rule_name, wait=True, safe=False):
        self.set_rule_state(rule_name=rule_name, state=RuleStates.DISABLED.value,
                            wait=wait, safe=safe)

    @allure.step("Set policy rule state")
    def set_rule_state(self, rule_name, state, wait=True, safe=False,
                       wait_sec=None):
        is_in_expected_mode = True if self.get_rule_state(rule_name=rule_name) == state else False
        wait_sec = wait_sec or WAIT_AFTER_SET_RULE_ACTION_STATE
        if is_in_expected_mode:
            assert safe, f"{self}' rule '{rule_name}' already {state} state !"
            logger.info(f"{self}' rule '{rule_name}' already {state} state !")
        else:

            logger.info(f"Set {self}'s rule '{rule_name}' to {state} state")
            self._rest_client.policies.set_policy_rule_state(policy_name=self.name, rule_name=rule_name,
                                                             state=state)
            if wait:
                logger.info(f"Sleep {wait_sec} seconds after set rule state")
                time.sleep(wait_sec)

    @allure.step("Set policy rule action to Log")
    def set_rule_action_to_log(self, rule_name, wait=True, safe=False):
        self.set_rule_action(rule_name=rule_name, action=RuleActions.LOG.value,
                             wait=wait, safe=safe)

    @allure.step("Set policy rule action to Block")
    def set_rule_action_to_block(self, rule_name, wait=True, safe=False):
        self.set_rule_action(rule_name=rule_name, action=RuleActions.BLOCK.value,
                             wait=wait, safe=safe)

    @allure.step("Set policy rule action")
    def set_rule_action(self, rule_name, action, wait=True, safe=False,
                        wait_sec=None):
        is_in_expected_mode = True if self.get_rule_action(rule_name=rule_name) == action else False
        wait_sec = wait_sec or WAIT_AFTER_SET_RULE_ACTION_STATE
        if is_in_expected_mode:
            assert safe, f"{self}'s rule '{rule_name}' already in {action} action !"
            logger.info(f"{self}'s rule '{rule_name}' already in {action} action !")
        else:
            logger.info(f"Set {self}'s rule '{rule_name}' to {action} action")
            self._rest_client.policies.set_policy_rule_action(policy_name=self.name, rule_name=rule_name,
                                                              action=action)
            if wait:
                logger.info(f"Sleep {wait_sec} seconds after set rule action")
                time.sleep(wait_sec)


def set_policies_rule_state_to_disabled(policies: list[Policy], rule_name):
    policies_rules_states = []
    for policy in policies:
        policy_rule_state = (policy, rule_name, RuleStates.DISABLED.value)
        policies_rules_states.append(policy_rule_state)
    set_policies_rules_states(policies_rules_states=policies_rules_states)


def set_policies_rule_state_to_enabled(policies: list[Policy], rule_name):
    policies_rules_states = []
    for policy in policies:
        policy_rule_state = (policy, rule_name, RuleStates.ENABLED.value)
        policies_rules_states.append(policy_rule_state)
    set_policies_rules_states(policies_rules_states=policies_rules_states)


def set_policies_rules_states(policies_rules_states: List[tuple]):
    """
    policies_rules_states is a list of tuples (policy, rule_name, state)
    """
    for policy, rule_name, state in policies_rules_states:
        logger.info(f"Update policy '{policy}', rule '{rule_name}' state to {state}")
        policy.set_rule_state(rule_name=rule_name, state=state, wait=False, safe=True)
    logger.info(f"Sleep {WAIT_AFTER_SET_RULE_ACTION_STATE} seconds after set rules states")
    time.sleep(WAIT_AFTER_SET_RULE_ACTION_STATE)


def set_policies_to_prevention(policies: List[Policy]):
    for policy in policies:
        policy.set_to_prevention_mode(safe=True, wait=False)
    logger.info(f"Sleep {WAIT_AFTER_SET_POLICY_MODE} seconds after set policies mode to prevention")
    time.sleep(WAIT_AFTER_SET_POLICY_MODE)

