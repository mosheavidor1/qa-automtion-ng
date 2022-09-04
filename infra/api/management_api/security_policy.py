from enum import Enum
import logging
from ensilo.platform.rest.nslo_management_rest import NsloRest
import time
from infra.api.management_api.base_policy import BasePolicy, WAIT_AFTER_SET_RULE_ACTION_STATE
from infra.api.nslo_wrapper.rest_commands import RestCommands
import allure
logger = logging.getLogger(__name__)


class DefaultPoliciesNames(Enum):
    EXECUTION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXECUTION_PREVENTION
    EXFILTRATION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION
    RANSOMWARE_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION


class ExternalPoliciesNames(Enum):
  DEVICE_CONTROL = 'Device Control'
  EXTENDED_DETECTION = 'eXtended Detection'


class RulesNames(Enum):
    MALICIOUS_FILE_DETECTED = 'Malicious File Detected'
    STACK_PIVOT = 'Stack Pivot'
    DYNAMIC_CODE = 'Dynamic Code'
    UNCONFIRMED_EXECUTABLE = 'Unconfirmed Executable'


class RuleActions(Enum):
    BLOCK = 'Block'
    LOG = 'Log'


class SecurityPolicy(BasePolicy):
    """ A wrapper of our internal rest client for working with security policies.
        Each policy will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data, policy_rest=rest_client.policies)

    def __repr__(self):
        return f"Security Policy {self.name} in '{self.get_organization_name(from_cache=True)}'"

    @allure.step("Set security policy rule action to Log")
    def set_rule_action_to_log(self, rule_name, wait=True, safe=False):
        self.set_rule_action(rule_name=rule_name, action=RuleActions.LOG.value,
                             wait=wait, safe=safe)

    @allure.step("Set security policy rule action to Block")
    def set_rule_action_to_block(self, rule_name, wait=True, safe=False):
        self.set_rule_action(rule_name=rule_name, action=RuleActions.BLOCK.value,
                             wait=wait, safe=safe)

    @allure.step("Set security policy rule action")
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




