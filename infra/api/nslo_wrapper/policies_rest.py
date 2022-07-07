import json
from typing import List
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality


class PoliciesRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)
        
    def get_policies(self) -> List[dict]:
        status, response = self._rest.policies.ListPolicies()
        assert status, f'Could not get response from the management. \n{response}'
        policies = json.loads(response.text)
        return policies

    def set_policy_mode(self, name, mode):
        status, response = self._rest.policies.SetPolicyMode(policyName=name, mode=mode)
        assert status, f'Could not get response from the management. \n{response}'

    def assign_policy(self, policy_name, group_name):
        status, response = self._rest.policies.AssignCollector(policy_name, group_name)
        assert status, f'Could not get response from the management. \n{response}'
