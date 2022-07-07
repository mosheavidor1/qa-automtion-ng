import logging
import allure
import time
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
from ensilo.platform.rest.nslo_management_rest import NsloRest
logger = logging.getLogger(__name__)

WAIT_AFTER_ASSIGN = 60  # time to wait for collector configuration to be uploaded


class PolicyFieldsNames(Enum):
    """ Policy's fields names as we get from server """
    NAME = 'name'
    ORGANIZATION = 'organization'
    OPERATION_MODE = 'operationMode'
    COLLECTORS_GROUPS = 'agentGroups'


class DefaultPoliciesNames(Enum):
    EXECUTION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXECUTION_PREVENTION
    EXFILTRATION_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION
    RANSOMWARE_PREVENTION = NsloRest.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION


class ModeNames(Enum):
    PREVENTION = NsloRest.NSLO_PREVENTION_MODE
    SIMULATION = NsloRest.NSLO_SIMULATION_MODE


class Policy(BaseApiObj):
    """ A wrapper of our internal rest client for working with policies.
        Each policy will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._name = initial_data[PolicyFieldsNames.NAME.value]  # Static, unique identifier

    def __repr__(self):
        return f"Policy {self.name} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def name(self) -> int:
        return self._name

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = PolicyFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_operation_mode(self, from_cache=None, update_cache=True):
        field_name = PolicyFieldsNames.OPERATION_MODE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

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
    def assign_to_collector_group(self, group_name, wait_sec=None):
        """
        :param wait_sec: time to wait for collector configuration to be uploaded
        :param group_name: string, the name of the group that the policy will be assigned to.
        """
        logger.info(f"Assign {self} to the collector group {group_name}")
        self.assign_to_collector_groups(groups_names=[group_name], wait_sec=wait_sec)

    @allure.step("Assign this policy to collector groups")
    def assign_to_collector_groups(self, groups_names: list, wait_sec=None):
        """
        :param wait_sec: time to wait for collector configuration to be uploaded
        :param groups_names: string list, list of the names of the groups that the policy will be assigned to.
        """
        wait_sec = wait_sec or WAIT_AFTER_ASSIGN
        logger.info(f"Assign {self} to these collector groups {groups_names}")
        self._rest_client.policies.assign_policy(policy_name=self.name, group_name=groups_names)
        logger.info(f"Sleep {wait_sec} seconds to wait for collector configuration to be uploaded")
        time.sleep(wait_sec)

    @allure.step("Set policy to prevention mode")
    def set_to_prevention_mode(self, safe=False):
        is_in_prevention = True if self.get_operation_mode() == ModeNames.PREVENTION.value else False
        if is_in_prevention:
            assert safe, f"{self} already in prevention mode !"
        else:
            logger.info(f"Set {self} to prevention mode")
            self._rest_client.policies.set_policy_mode(name=self.name, mode=ModeNames.PREVENTION.value)
