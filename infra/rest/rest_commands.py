import time

import allure
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
        status, response = self.rest.inventory.ListCollectors(organization=organization)
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

    def set_system_mode(self, prevention):
        """
        :param prevention: boolean, True for prevention mode or False for simulation.
        """
        if prevention:
            status, response = self.rest.admin.SetSystemModePrevention()
        else:
            status, response = self.rest.admin.SetSystemModeSimulation()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            Reporter.report(f'Successfully changed system mode')
            return True

    def create_group(self, name, organization=None):
        """
        :param name: string, the name of the group.
        :return: True if succeeded creating the group, False if failed.
        """
        group_status, group_response = self.rest.inventory.ListCollectorGroups(organization=organization)
        groups_list = self._get_info(group_status, group_response)

        for group in groups_list:
            if name == group["name"]:
                Reporter.report('group ' + name + ' already exist')
                return True

        status, response = self.rest.inventory.CreateCollectorGroup(name, organization)

        group_status, group_response = self.rest.inventory.ListCollectorGroups(organization=organization)
        groups_list = self._get_info(group_status, group_response)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        result = False
        for group in groups_list:
            if name in group["name"]:
                result = True
        assert result

        Reporter.report('Created the group ' + name + ' successfully.')
        return True

    def move_collector(self, validation_data, group_name):
        """
        :param validation_data: dictionary, the data of the collector to be moved.
        :param group_name: string, the name of the group to move the collector to.
        :return: True if succeeded, False if failed.
        """
        collector_name = list(map(lambda x: list(x.values())[0], self.get_collector_info(validation_data, 'name')))
        status, response = self.rest.inventory.MoveCollectors(collector_name, group_name)
        collector_group = self.get_collector_info(validation_data, 'collectorGroupName')
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if collector_group[0]["collectorGroupName"] != group_name:
            assert False, 'Could not move the collector ' + str(
                collector_name) + ' to the group ' + group_name + '.'

        Reporter.report(
            'Moved the collector ' + str(collector_name) + ' to the group ' + group_name + ' successfully.')
        return True

    """ ************************************************ Events ************************************************ """

    @allure.step("Get security events")
    def get_security_events(self,
                            validation_data,
                            timeout=60,
                            sleep_delay=2,
                            fail_on_no_events=True):
        """
        :param validation_data: dictionary of the data to get.
                                options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
                                fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
                                Action, rule, strictMode.

        :return: list of dictionaries with the event info.
                 if the request failed or there were no events found -> False
        """

        start_time = time.time()
        is_found = False
        error_message = None
        events = []
        while time.time() - start_time < timeout and not is_found:
            try:
                status, response = self.rest.events.ListEvents(**validation_data)
                if not status:
                    error_message = f'Could not get response from the management. \n{response}'

                events = loads(response.text)
                if not len(events):
                    error_message = 'No event with the given parameters found.'
                    time.sleep(sleep_delay)
                else:
                    is_found = True
                    Reporter.report(f'Successfully got information of {len(events)} events.')

            except Exception as e:
                Reporter.report(f'{error_message}, trying again')
                time.sleep(sleep_delay)

        if not is_found and fail_on_no_events:
            assert False, f"{error_message} after waiting {timeout} seconds"

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
        if len(eventsIds):
            return self.delete_events(eventsIds)
        else:
            Reporter.report('There is no events to delete with the given name.')
            return False

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

    @allure.step("Delete all events")
    def delete_all_events(self, timeout=60):
        event_ids = []
        response = self.rest.events.ListEvents()
        as_list_of_dicts = json.loads(response[1].text)
        for single_event in as_list_of_dicts:
            event_id = single_event.get('eventId')
            event_ids.append(event_id)

        if len(event_ids) > 0:
            self.rest.events.DeleteEvents(eventIds=event_ids)
            time.sleep(timeout)

        else:
            Reporter.report("No events, nothing to delete")

    """ ************************************************ Exceptions ************************************************ """

    def create_exception(self, eventId, groups=None, destinations=None, organization="Default", useAnyPath=None,
                         useInException=None, wildcardFiles=None, wildcardPaths=None, **kwargs):
        """
          create exception
          :param eventId: event id for create exception
          :param groups: list of string or None for all groups
          :param destinations: list of destinations or None for all destinations
          :param organization: string or none for all organizations
          :param useAnyPath: useAnyPath
          :param useInException: useInException
          :param wildcardFiles: wildcardFiles
          :param wildcardPaths: wildcardPaths
          :return: True or False.
          """

        url = "/events/create-exception"
        kwargs["eventId"] = eventId
        if groups:
            kwargs["collectorGroups"] = groups
            kwargs["allCollectorGroups"] = False
        else:
            kwargs["allCollectorGroups"] = True
        if destinations:
            kwargs["destinations"] = destinations
            kwargs["allDestinations"] = False
        else:
            kwargs["allDestinations"] = True
        if organization:
            kwargs["organization"] = organization
            kwargs["allOrganizations"] = False
        else:
            kwargs["allOrganizations"] = True

        body = {}
        if useAnyPath:
            body["useAnyPath"] = useAnyPath
        if useInException:
            body["useInException"] = useInException
        if wildcardFiles:
            body["wildcardFiles"] = wildcardFiles
        if wildcardPaths:
            body["wildcardPaths"] = wildcardPaths

        response, status = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=kwargs, body=body)
        if status:
            return True
        else:
            assert False, f"failed to create exception, error: {response}"

    def get_exceptions(self, event_id=None):
        """
        :param event_id: string, optional, if no event id given returns all the exceptions
        :return: dictionary or list of dictionaries (if no event id given) with the following parameters:
                    exceptionId, originEventId, userName, updatedAt, createdAt, comment, selectedDestinations,
                    optionalDestinations, selectedCollectorGroups, optionalCollectorGroups, alerts.
        """
        if event_id:
            status, response = self.rest.exceptions.GetEventExceptions(event_id)
        else:
            status, response = self.rest.exceptions.ListExceptions()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if event_id:
            exceptions = loads(response.text)[0]
        else:
            exceptions = loads(response.text)

        Reporter.report(f'Successfully got information of the following event id: {event_id}.')
        return exceptions

    @allure.step("Delete all exceptions")
    def delete_all_exceptions(self, timeout=60):
        exception_ids = []
        response = self.rest.exceptions.ListExceptions()
        as_list_of_dicts = json.loads(response[1].text)
        for single_exception in as_list_of_dicts:
            event_id = single_exception.get('exceptionId')
            exception_ids.append(event_id)

        if len(exception_ids) > 0:
            for exc_id in exception_ids:
                self.rest.exceptions.DeleteException(exceptionId=exc_id)
            time.sleep(timeout)
        else:
            Reporter.report("No execptions, nothing to delete")

    """ ************************************************ Policies ************************************************ """

    def get_policy_info(self, validation_data=None, output_parameters=None, organization=None):
        """
        :param validation_data: string, the data about the wanted policy.
        :param output_parameters: string or list, the parameters to get from the given policy.
               parameter options: 'name', 'operationMode', 'agentGroups', 'rules'.
        :return: list of dictionaries, the information for the given data.
        """
        status, response = self.rest.policies.ListPolicies(organization=organization)
        return self._get_info(status, response, 'policy', validation_data, output_parameters)

    def set_policy_mode(self, name, mode, organization=None):
        """
        :param name: string, the policy name.
        :param mode: string, 'Prevention' or 'Simulation'.
        :return: True if succeeded, False if failed.
        """
        status, response = self.rest.policies.SetPolicyMode(name, mode, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Changed the policy ' + name + 'mode to: ' + mode + '.')
        return status

    def assign_policy(self, policy_name, group_name, timeout=60, organization=None):
        """
        :param timeout: time to wait for collector configuration to be uploaded
        :param policy_name: string, the name of the policy to assign,
        :param group_name: string or list, the name of the group that the policy will be assigned to.
        :return: True if succeeded, False if failed.
        """
        status, response = self.rest.policies.AssignCollector(policy_name, group_name, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        Reporter.report(f"Assigned the policy {policy_name} to the group {group_name} successfully")
        time.sleep(timeout)
        return True

