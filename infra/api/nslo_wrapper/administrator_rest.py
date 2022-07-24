import json

from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality


class AdministratorRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)
    
    def get_system_summery(self, parameter=None, log=False, organization='All organizations'):
        """
        :param parameter: string or list, the information parameter to get from the system summery.
        :param log: boolean, True to log the full system summery.
        :return: string, the information for the given parameter.
        """
        if isinstance(parameter, str):
            parameter = [parameter]

        status, response = self._rest.admin.GetSystemSummary(organization=organization)
        self._validate_expected_status_code(expected_status_code=200,
                                            actual_status_code=response.status_code,
                                            error_message=f"Get system summary - expected response code: {200}, actual: {response.status_code}")

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        summery = json.loads(response.text)

        if parameter:
            summery = self._filter_data([summery], parameter)
            if summery:
                return summery[0]

        return summery

    def set_system_mode(self, prevention: bool):
        """
        :param prevention: boolean, True for prevention mode or False for simulation.
        """
        if prevention:
            status, response = self._rest.admin.SetSystemModePrevention()
        else:
            status, response = self._rest.admin.SetSystemModeSimulation()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            Reporter.report(f'Successfully changed system mode')
            return True