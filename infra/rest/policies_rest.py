import time

from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.rest.base_rest_functionality import BaseRestFunctionality


class PoliciesRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)
        
    def get_policy_info(self, validation_data=None, output_parameters=None):
        """
        :param validation_data: string, the data about the wanted policy.
        :param output_parameters: string or list, the parameters to get from the given policy.
               parameter options: 'name', 'operationMode', 'agentGroups', 'rules'.
        :return: list of dictionaries, the information for the given data.
        """
        status, response = self._rest.policies.ListPolicies()
        return self._get_info(status, response, 'policy', validation_data, output_parameters)

    def set_policy_mode(self, name, mode):
        """
        :param name: string, the policy name.
        :param mode: string, 'Prevention' or 'Simulation'.
        :return: True if succeeded, False if failed.
        """
        status, response = self._rest.policies.SetPolicyMode(policyName=name, mode=mode)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Changed the policy ' + name + 'mode to: ' + mode + '.')
        return status

    def assign_policy(self, policy_name, group_name, timeout=60):
        """
        :param timeout: time to wait for collector configuration to be uploaded
        :param policy_name: string, the name of the policy to assign,
        :param group_name: string or list, the name of the group that the policy will be assigned to.
        :return: True if succeeded, False if failed.
        """
        status, response = self._rest.policies.AssignCollector(policy_name, group_name)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        Reporter.report(f"Assigned the policy {policy_name} to the group {group_name} successfully")
        time.sleep(timeout)
        return True

    def turn_on_prevention_mode(self):
        self.set_policy_mode(name=self._rest.policies.NSLO_POLICY_EXECUTION_PREVENTION,
                             mode=self._rest.NSLO_PREVENTION_MODE)

        self.set_policy_mode(name=self._rest.policies.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION,
                             mode=self._rest.NSLO_PREVENTION_MODE)

        self.set_policy_mode(name=self._rest.policies.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION,
                             mode=self._rest.NSLO_PREVENTION_MODE)