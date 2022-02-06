from ensilo.platform.rest.nslo_management_rest import NsloManagementConnection, NsloRest
from json import loads
import json
from infra.allure_report_handler.reporter import Reporter


class RestCommands(object):
    """
    Class with different rest API methods.
    """

    def __init__(self, management_ip, management_user, management_password, organization=None):
        self.management_ip = management_ip
        self.management_user = management_user
        self.management_password = management_password
        self.rest = NsloRest(NsloManagementConnection(management_ip, management_user, management_password,
                                                      organization=organization))

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

        components = loads(response.text)

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

    def get_collector_info(self, validation_data=None, output_parameters=None, organization=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given collector.
                                  options for collector parameters: 'id', 'name', 'collectorGroupName', 'operatingSystem',
                                                             'ipAddress' (0.0.0.0), 'osFamily', 'state', 'lastSeenTime',
                                                              'version', 'macAddresses', 'loggedUsers'
        :param validation_data: dictionary, the data to get from the collector.
        :return: according to the get_info function.
        """
        if organization:
            status, response = self.rest.inventory.ListCollectors(organization=organization)
        else:
            status, response = self.rest.inventory.ListCollectors()
        return self._get_info(status, response, 'collector', validation_data, output_parameters)

    def get_aggregator_info(self, validation_data=None, output_parameters=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given core.
                                  options for collector parameters: 'id', 'hostName', 'ipAddress', 'version',
                                  'numOfAgents', 'numOfDownAgents', 'state'.
        :param validation_data: dictionary, the data to get from the core.
        :return: according to the get_info function.
        """
        status, response = self.rest.inventory.ListAggregators()
        return self._get_info(status, response, 'aggregator', validation_data, output_parameters)

    def get_core_info(self, validation_data=None, output_parameters=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given core.
                                  options for collector parameters: ['deploymentMode', 'ip' ('0.0.0.0:555'), 'name',
                                  'version', 'status']
        :param validation_data: dictionary, the data to get from the core.
        :return: according to the get_info function.
        """
        status, response = self.rest.inventory.ListCores()
        return self._get_info(status, response, 'core', validation_data, output_parameters)

    def get_security_events(self, validation_data):
        """
        :param validation_data: dictionary of the data to get.
                                options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
                                fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
                                Action, rule, strictMode.

        :return: list of dictionaries with the event info.
                 if the request failed or there were no events found -> False
        """

        status, response = self.rest.events.ListEvents(**validation_data)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        events = loads(response.text)
        if not len(events):
            assert False, 'No event with the given parameters found.'
        else:
            Reporter.report(f'Successfully got information of {len(events)} events.')

            return events

    def delete_event_by_name(self, eventName):
        urlget = "/events/list-events"
        response = self.rest.passthrough.ExecuteRequest(urlget, mode='get', inputParams=None)[1].text
        eventsList = json.loads(response)
        eventsIds = []
        for item in eventsList:
            try:
                name = item["process"]
                if eventName in str(name):
                    eventsIds.append(item["eventId"])
            except:
                pass
        return self.delete_events(eventsIds)

    def delete_events(self, event_ids):
        """
        :param event_ids: list of strings or string.
        """
        status, response = self.rest.events.DeleteEvents(event_ids)
        event_info = self.get_security_events({'Event ID': event_ids})
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if event_info:
            assert False, 'Could not delete the given events.'

        Reporter.report('Deleted the given events successfully.')
        return True


    def get_system_summery(self, parameter=None, log=False):
        """
        :param parameter: string or list, the information parameter to get from the system summery.
        :param log: boolean, True to log the full system summery.
        :return: string, the information for the given parameter.
        """
        if isinstance(parameter, str):
            parameter = [parameter]

        status, response = self.rest.admin.GetSystemSummary()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        summery = loads(response.text)

        if parameter:
            summery = self._filter_data([summery], parameter)
            if summery:
                return summery[0]

        return summery