import json
from ensilo.platform.rest.nslo_management_rest import NsloRest


class BaseRestFunctionality:

    def __init__(self, nslo_rest: NsloRest):
        self._rest = nslo_rest

    def _validate_expected_status_code(self,
                                       expected_status_code: int,
                                       actual_status_code: int,
                                       error_message: str):
        if expected_status_code != actual_status_code:
            if not (expected_status_code == 200 and actual_status_code == 201):
                assert False, error_message

    def _validate_data(self, raw_data, validating_data):
        """
        Checks if validating_data in raw data.
        :param raw_data: list of dictionaries, not filtered data.
        :param validating_data: dictionary, data used to validate.
        :return: list of the validated dictionaries.
        """

        filtered_components = []
        for component in raw_data:
            if all(item in component.items() for item in validating_data.items()):
                filtered_components.append(component)
        return filtered_components

    def _get_info(self, status, response, section="", validation_data={}, output_parameters=[]):
        """
        general function to all the get info functions.
        :param validation_data: dictionary of the data to search, matches parameter to its data. {'ip':'0.0.0.0', 'name': 'name'}
        :param output_parameters: string or list, the parameters to get from the component.
        :param section: string, the component section. options: 'policy' or 'collector'.
        :param status: status from the request.
        :param response: the response from the request.
        :return: if the operation failed -> False
                 if there were no given data -> the whole list of data in that section.
                 if there was only one parameter -> string, the information
                 if there is a list of parameters -> dictionary, the information that matches to the given name and parameter.
        """

        if not status:
            if not isinstance(response, str):
                response = response.text
            assert False, f'Could not get response from the management. \n{response}'

        if isinstance(output_parameters, str):
            output_parameters = [output_parameters]

        components = json.loads(response.text)

        if not validation_data and not output_parameters:
            return components
        elif not validation_data and output_parameters:
            return self._filter_data(components, output_parameters)

        filtered_components = self._validate_data(components, validation_data)
        if not len(filtered_components):
            assert False, 'Could not find the ' + section + ' with the data: ' + str(validation_data)

        if not output_parameters:
            return filtered_components
        else:
            return self._filter_data(filtered_components, output_parameters)

    def _filter_data(self, raw_data, parameters):
        """
        filter data by given parameters
        :param raw_data: list of dictionaries.
        :param parameters: list.
        :return: list of filtered dictionaries.
        """
        return_list = []

        for component in raw_data:
            component_dict = {}
            for parameter in parameters:
                if parameter in component.keys():
                    component_dict[parameter] = component[parameter]
                else:
                    assert False, f'Could not get the information, the given parameter: {parameter} does not exist. The options are: {list(component.keys())}'

        if component_dict:
            return_list.append(component_dict)

        if return_list:
            return return_list

        else:
            assert False, f'Could not get the information: {raw_data} based on the given parameters: {parameters}.'