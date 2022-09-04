import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
import json
from typing import List
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality
import logging
logger = logging.getLogger(__name__)


class CommunicationControlRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    def get_policies(self, expected_status_code: int = 200) -> List[dict]:
        url = '/comm-control/list-policies'
        params = {}
        status, response = self._rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams=params)
        assert status, f"Failed to get comm control policies, got error: {response}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f'Failed to get comm control policies, got error: {response}')
        policies = json.loads(response.text)
        logger.debug(f"Found these comm control policies: \n {policies}")
        return policies

    @allure.step("API- Set comm control policy {name} to mode {mode}")
    def set_policy_mode(self, name, mode, expected_status_code: int = 200):
        logger.info(f"API- Set comm control policy {name} to mode {mode}")
        status, response = self._rest.commControl.SetPolicyMode(policyNames=name, mode=mode)
        assert status, f'Failed to set comm control policy {name} to mode {mode}, got error: {response}'
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f'Failed to set comm control policy {name} to mode {mode}, got error: {response}')

    @allure.step("API- Assign comm control policy {policy_name} to group {group_name}")
    def assign_policy(self, policy_name, group_name, expected_status_code: int = 200):
        logger.info(f"API- Assign comm control policy {policy_name} to group {group_name}")
        status, response = self._rest.commControl.AssignCollectorToPolicy(collectorGroups=group_name,
                                                                          policy=policy_name)
        assert status, f'Failed to assign comm control policy {policy_name} to group {group_name}'
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f'Failed to assign comm control policy {policy_name} to group {group_name}')

    @allure.step("API- Set comm control policy's '{policy_name}' rule '{rule_name}' to {state} state")
    def set_policy_rule_state(self, policy_name, rule_name, state, expected_status_code: int = 200):
        url = '/comm-control/set-policy-rule-state'
        params = {'policyName': policy_name, 'ruleName': rule_name, 'state': state}
        logger.info(f"API- Set comm control policy's '{policy_name}' rule '{rule_name}' to {state} state")
        status, response = self._rest.passthrough.ExecuteRequest(url=url, mode="put", inputParams=params)
        assert status, f"Failed to set policy's '{policy_name}' rule '{rule_name}' to {state} state, got error: " \
                       f"{response}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Failed to set policy's '{policy_name}' rule '{rule_name}' to {state} state, got error: {response}")


