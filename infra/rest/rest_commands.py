from time import sleep
from ensilo.platform.rest.nslo_management_rest import NsloManagementConnection, NsloRest
from json import loads
import os
import json
import ast
from spnego.__main__ import yaml
from infra.allure_report_handler.reporter import Reporter

class RestCommands(object):
    """
    Class with different rest API methods.
    The username and password refer to those of the UI.
    using example:
                test = RestCommands('1.2.3.4', 'username', 'password')
                collector_ip = test.get_collector_info('Collector_name', 'IP')
                test.upload_content('path\to\content\file.nslo')
    """

    def __init__(self, management_ip, management_user, management_password, organization=None):
        self.management_ip = management_ip
        self.management_user = management_user
        self.management_password = management_password
        # self.verification_code = None
        self.rest = NsloRest(NsloManagementConnection(management_ip, management_user, management_password,
                                                      organization=organization))

    # Locators
    _events_translate_dict = {'Event ID': 'eventIds', 'Device': 'device', 'Collector Group': 'collectorGroups',
                              'Process': 'process', 'Destinations': 'destinations', 'Action': 'actions',
                              'Path': 'ProcessPath', 'First Seen': 'firstSeen', 'Last Seen': 'lastSeen',
                              'Event Status': 'handled', 'Rules': 'rules'}
    _events_reversed_translate_dict = {'eventId': 'Event ID', 'collectorGroups': 'Collector Group',
                                       'process': 'Process', 'destinations': 'Destinations', 'action': 'Action',
                                       'processPath': 'Path', 'firstSeen': 'First Seen', 'lastSeen': 'Received',
                                       'handled': 'Event Status', 'rules': 'Rules', 'classification': 'Classification'}

    """ *********************************************** Inventory *********************************************** """

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

    def get_collector_state(self, name=None, ip=None, organization=None):
        """
        :param name: str, name of the component.
        :param ip: str, the ip address of the component.
        :return: according to get value function.
        """
        # getting raw state
        output_parameters = ['state', 'ipAddress']
        if name is not None:
            output_parameters[1] = 'name'
        raw_data = self.get_collector_info(output_parameters=output_parameters, organization=organization)
        return self._get_values(name, ip, raw_data)

    def get_collector_version(self, name=None, ip=None):
        """
        :param name: str, name of the component.
        :param ip: str, the ip address of the component.
        :return: according to get value function.
        """
        # getting raw version
        output_parameters = ['version', 'ipAddress']
        if name is not None:
            output_parameters[1] = 'name'
        raw_data = self.get_collector_info(output_parameters=output_parameters)
        return self._get_values(name, ip, raw_data)

    def delete_collectors(self, validation_data):
        """
        :param validation_data: dictionary, the data of the collectors to delete.
        :return: if the collectors weren't in the management from the beginning -> True
                 if the collectors were deleted successfully -> True
                 if failed deleting the collectors -> False
        """
        collectors_before = self.get_collector_info(output_parameters=list(validation_data.keys()))
        if validation_data not in collectors_before:
            Reporter.report('The collectors with the given data: ' + str(
                validation_data) + ' does not exist, the current collectors list is: ' + str(collectors_before))
            return True
        collector_name = list(map(lambda x: list(x.values())[0], self.get_collector_info(validation_data, 'name')))
        status, response = self.rest.inventory.DeleteCollectors(collector_name)
        collectors_after = self.get_collector_info(output_parameters=list(validation_data.keys()))
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if validation_data in collectors_after:
            assert False, 'Could not delete the collectors: ' + str(collector_name) + ' from the management.'

        Reporter.report('Deleted the collectors: ' + str(collector_name) + ' from the management successfully.')
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
            assert False, 'Could not move the collector ' + str(collector_name) + ' to the group ' + group_name + '.'

        Reporter.report('Moved the collector ' + str(collector_name) + ' to the group ' + group_name + ' successfully.')
        return True

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

    def get_core_state(self, name=None, ip=None):
        """
        :param name: str, name of the component.
        :param ip: str, the ip address of the component.
        :return: according to get value function.
        """
        # getting raw state
        output_parameters = ['status', 'ip']
        if name is not None:
            output_parameters[1] = 'name'
        raw_data = self.get_core_info(output_parameters=output_parameters)

        return self._get_values(name, ip, raw_data)

    def get_core_version(self, name=None, ip=None):
        """
        :param name: str, name of the component.
        :param ip: str, the ip address of the component.
        :return: according to get value function.
        """
        # getting raw version
        output_parameters = ['version', 'ip']
        if name is not None:
            output_parameters[1] = 'name'
        raw_data = self.get_core_info(output_parameters=output_parameters)

        return self._get_values(name, ip, raw_data)

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

    def create_group(self, name, organization=None):
        """
        :param name: string, the name of the group.
        :return: True if succeeded creating the group, False if failed.
        """
        group_status, group_response = self.rest.inventory.ListCollectorGroups(organization=organization)
        groups_list = self._get_info(group_status, group_response)

        for group in groups_list:
            if name == group["name"]:
                return True

        if organization:
            status, response = self.rest.inventory.CreateCollectorGroup(name, organization)
        else:
            status, response = self.rest.inventory.CreateCollectorGroup(name)
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

    def get_collector_groups_info(self, organization=None):
        status, response = self.rest.passthrough.ExecuteRequest(url="/inventory/list-collector-groups",
                                                                mode="get",
                                                                inputParams={"organization": organization})
        if status:
            return json.loads(response.text)
        else:
            return False

    def enable_disable_collector(self, enable, collectors, **kwargs):
        """
        Change Collector/s status
        :param enable: A mandatory true/false parameter indicating whether to enable (true) or disable (false) the collector
        :param collectors: Specifies the list of device names
        :return: True if succeeded creating the group, False if failed
        """
        status, response = self.rest.inventory.ToggleCollectors(enable, collectors, **kwargs)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'{enable} collectors state successfully')
        return True

    def get_collector_logs(self, device, device_type='NAME', zip_file_name=None, organization=None, path='c:\\qa'):
        """
        This operation results in a file stream (binary data), which is a .zip file
        device_type = 'NAME' or 'ID'
        device: if device_type = 'NAME' - Specifies the name of the collector
                if device_type = 'ID' - Specifies the ID of the collector
        :return:
        """
        status, response = self.rest.inventory.CollectorLogs(device, device_type, organization, timeout=180)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if not zip_file_name:
            zip_file_name = device

        logs_zip = open(path + '\\' + f'{zip_file_name}.zip', 'wb')
        logs_zip.write(response.content)
        logs_zip.close()

        Reporter.report(f'Collector {device} logs saved to: {logs_zip} successfully')
        return True

    def get_system_logs(self, zip_file_name=None, path='c:\\qa'):
        """
        This operation results in a file stream (binary data), which is a .zip file
        device_type = 'NAME' or 'ID'
        device: if device_type = 'NAME' - Specifies the name of the collector
                if device_type = 'ID' - Specifies the ID of the collector
        :return:
        """
        url = "/inventory/system-logs"
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams={})

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if not zip_file_name:
            zip_file_name = "systemlogs"

        logs_zip = open(path + '\\' + f'{zip_file_name}.zip', 'wb')
        logs_zip.write(response.content)
        logs_zip.close()

        Reporter.report(f'system logs saved to: {logs_zip} successfully')
        return True

    def get_core_logs(self, core_name, zip_file_name=None, path='c:\\qa'):
        """
        This operation results in a file stream (binary data), which is a .zip file
        device_type = 'NAME' or 'ID'
        device: if device_type = 'NAME' - Specifies the name of the collector
                if device_type = 'ID' - Specifies the ID of the collector
        :return:
        """
        url = "/inventory/core-logs"
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams={'device': core_name})

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if not zip_file_name:
            zip_file_name = "corelogs"

        logs_zip = open(path + '\\' + f'{zip_file_name}.zip', 'wb')
        logs_zip.write(response.content)
        logs_zip.close()

        Reporter.report(f'core logs saved to: {logs_zip} successfully')
        return True

    """ ************************************************* Admin ************************************************** """

    def upload_collectors_content(self, contentFile, path=r'\\ens-fs01\Versions\Collector_Content'):
        full_path = rf"{path}\{contentFile}"
        status = self.rest.admin.UploadContent(full_path)
        if not status:
            assert False, f'Could not get response from the management.'
        return True

    def upload_content(self, content_number):
        """
        :param content_number: string, number of content file.
        :return: True if the content uploaded successfully or if the content alreay exist.
                 False if the content failed uploading or if file dosnt exist.
        """
        current_content = self.get_system_summery('contentVersion')['contentVersion']
        Reporter.report('The current content version is: ' + str(current_content) + '.')
        if int(current_content) > int(content_number):
            Reporter.report("content number is too high, cant downgrade the current content")
            return False
        if current_content != content_number:
            os.system(r"net use \\ens-fs01 /user:ensilo\automation Aut0g00dqa42")
            files = os.listdir(r'\\ens-fs01\Versions\Content')
            contentFile = None
            for file in files:
                if content_number in file and "nslo" in file:
                    contentFile = file
                    break
            if contentFile is None:
                assert False, "content file not found"
            else:
                Reporter.report("uploading content file")
                path = r'\\ens-fs01\Versions\Content' + '\\' + contentFile
                status = self.rest.admin.UploadContent(path)
                if not status:
                    assert False, f'Could not get response from the management.'
                else:
                    new_content = self.get_system_summery('contentVersion')['contentVersion']
                    return new_content == content_number
        else:
            Reporter.report("content version match, no need to upload new content")
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

    def set_system_mode_prevention(self):

        status, response = self.rest.admin.SetSystemModePrevention()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            Reporter.report(f'Successfully set system mode to prevention mode')
            return True

    def set_system_mode_simulation(self):

        status, response = self.rest.admin.SetSystemModeSimulation()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            Reporter.report(f'Successfully set system mode to simulation mode')
            return True

    def get_system_version(self):
        return self.rest.admin.GetSystemVersion()

    """ ************************************************* Events ************************************************* """

    def get_system_events(self, validation_data=None):
        """
        returning the filtered data from the last 100 system events.
        :param validation_data: dictionary, matches parameter to string or tuple of strings with data to filter.
                     parameter options: 'componentName', 'componentType', 'description', 'date'
        :return: list of dictionaries with all the filtered data.
        """
        status, response = self.rest.systemEvents.ListSystemEvents()
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        system_events = loads(response.text)
        if validation_data is None:
            Reporter.report(f'Successfully got {len(system_events)} system events.')
            return system_events

        return_list = self._validate_data(system_events, validation_data)
        if len(return_list):
            Reporter.report(f'Successfully got {len(system_events)} system events.')
            return return_list
        else:
            assert False, 'There were no system events found with the given data.'

    def get_security_events(self, validation_data, translate_to_list_of_dictionaries=True):
        """
        :param validation_data: dictionary of the data to get.
                                options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
                                fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
                                Action, rule, strictMode.

        :return: list of dictionaries with the event info.
                 if the request failed or there were no events found -> False
        """

        status, response = self.rest.events.ListEvents(
            **self._translate_dictionary(validation_data, self._events_translate_dict))
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        event = loads(response.text)
        if not len(event):
            assert False, 'No event with the given parameters found.'
        else:
            Reporter.report(f'Successfully got information of {len(event)} events.')
            events = self._translate_list_of_dictionaries(event, self._events_reversed_translate_dict)

            if translate_to_list_of_dictionaries:
                events = self._translate_list_of_dictionaries(event, self._events_reversed_translate_dict)

            for event in events:
                event['Device'] = list(map(lambda x: x['device'], event['collectors']))
                event['Collector group'] = list(map(lambda x: x['collectorGroup'], event['collectors']))
                for event in events:
                    event['Device'] = list(map(lambda x: x['device'], event['collectors']))
                    event['Collector group'] = list(map(lambda x: x['collectorGroup'], event['collectors']))

            return events

    def get_event_json(self, event_id):
        """
        gets the json of the FIRST raw event from the event id given.
        :param event_id: string, the id of the event.
        :return: if failed getting response from management -> False
                 if got response successfully -> dictionary, the json of the given event.
                 return example: [{'processType': '32 bit', 'seen': True, 'comment': 'comment', 'certified': False,
                                   'archived': False, 'severity': 'Critical', 'loggedUsers': ['user1', 'user2'],
                                   'collectors': [{'lastSeen': 'date', 'ip': 'ip', 'collectorGroup': 'group',
                                                   'macAddresses': ['address'], 'id': id, 'device': 'device',
                                                   'operatingSystem': 'Windows 10 Enterprise 2016 LTSB'}],
                                   'action': 'Block', 'Event ID': id, 'Process': 'StackPivotTests.exe',
                                   'Destinations': ['destination1, destination2'], 'Path': 'path', 'First Seen': 'date',
                                   'Last Seen': 'date', 'Rules': ['Stack Pivot'], 'Classification': 'Malicious'}]

        """
        raw_events = self.get_event_RDI(event_id)
        raw_events_id = list(map(lambda x: x['EventId'], raw_events))
        raw_events_id = list(map(lambda x: str(x), raw_events_id))[0]
        json_status, json_response = self.rest.events.GetEventJson(raw_events_id)
        if not json_status:
            assert False, f'Could not get response from the management. \n{json_response}'
        json_event = loads(json_response.text)
        Reporter.report('Found the json of the given event.')
        return json_event

    def get_event_RDI(self, events_ids, organization='Default'):
        """
        Event raw data items.
        :param events_ids: str ot list of strings.
        :param organization: The name of the organization
        :return: list of dictionaries- each dictionary to each event id.
        """
        status, response = self.rest.events.ListRawDataItems(events_ids, organization=organization)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            events_RDI = loads(response.text)
            Reporter.report(f'Successfully got the raw data items of {len(events_RDI)} events.')
            return events_RDI

    def handle_events(self, events_ids, handled, organization=None):
        """
        :param events_ids: str or list of strings.
        :param handled: boolean, True to handle event, False to unhandle.
        """
        if organization:
            status, response = self.rest.events.SetEventsHandled(events_ids, handled=handled, organization=organization)
        else:
            status, response = self.rest.events.SetEventsHandled(events_ids, handled=handled)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        return True

        #  The code below has been commented out due to verification not working.

        # is_handled = self._filter_data(self.get_security_events({'Event ID': events_ids}), ['handled'])
        # if all(item['handled'] for item in is_handled) == handled:
        #     Reporter.report(f'Successfully handled {len(is_handled)} events.')
        #     return True
        # else:
        #     assert False,f'Could not handle {len(is_handled)} events.'

    def set_events_read(self, events_ids, read, organization=None):
        """
        :param events_ids: str or list of strings.
        :param handled: boolean, True to handle event, False to unhandle.
        """
        if organization:
            status, response = self.rest.events.SetEventsRead(events_ids, read=read, organization=organization)
        else:
            status, response = self.rest.events.SetEventsRead(events_ids, read=read)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        return True

    def count_events(self, validation_data):
        """
        :param validation_data: dictionary of the data to get.
                                options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
                                fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
                                Action, rule, strictMode.
        :return: string with the count.
        """
        status, response = self.rest.events.CountEvents(**validation_data)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            count = response.text
            Reporter.report(f'Successfully found {count} events.')
            return count

    def set_events_classification(self, events_ids, classification):
        """
        :param events_ids: str or list of strings.
        :param str, classification: Malicious, Safe, PUP or the original event classification.
        """
        status, response = self.rest.events.SetEventsClassification(events_ids, classification)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        else:
            Reporter.report(f'Successfully set the classification of the events: {events_ids} to: {classification}.')
            return True

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

    def delete_all_events(self):
        """
        :return: True if succeeded deleting all the events, False if failed.
        """
        status, response = self.rest.events._DeleteAllEvents()
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Deleted all events successfully.')
        return True

    """ ************************************************ Policies ************************************************ """

    def get_policy_info(self, validation_data=None, output_parameters=None, organization=None):
        """
        :param validation_data: string, the data about the wanted policy.
        :param output_parameters: string or list, the parameters to get from the given policy.
               parameter options: 'name', 'operationMode', 'agentGroups', 'rules'.
        :return: list of dictionaries, the information for the given data.
        """
        if organization:
            status, response = self.rest.policies.ListPolicies(organization=organization)
        else:
            status, response = self.rest.policies.ListPolicies()
        return self._get_info(status, response, 'policy', validation_data, output_parameters)

    def set_policy_mode(self, name, mode, organization=None):
        """
        :param name: string, the policy name.
        :param mode: string, 'Prevention' or 'Simulation'.
        :return: True if succeeded, False if failed.
        """
        if organization:
            status, response = self.rest.policies.SetPolicyMode(name, mode, organization)
        else:
            status, response = self.rest.policies.SetPolicyMode(name, mode)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Changed the policy ' + name + 'mode to: ' + mode + '.')
        return status

    def set_rule_mode(self, policy_name, rule_name, action=None, state=None, organization=None):
        """
        method to change rules action or state
        :param policy_name: string.
        :param rule_name: string, full rule name.
        :param action: string, options to change action: 'Block' or 'Log'.
        :param state: string, option to change state: 'Enabled' or 'Disabled'.
        :return: True if succeeded, False if failed.
        """
        try:
            partial_rule_name = rule_name.split(' -')[0]
            if action:
                if organization:
                    action_status, action_response = self.rest.policies.SetPolicyRuleAction(policy_name,
                                                                                            partial_rule_name,
                                                                                            action,
                                                                                            organization=organization)
                else:
                    action_status, action_response = self.rest.policies.SetPolicyRuleAction(policy_name,
                                                                                            partial_rule_name,
                                                                                            action)
                if not action_status:
                    raise Exception(
                        f'Could not get response from the management when tried to change the action. \n{action_response}')

            if state:
                if organization:
                    state_status, state_response = self.rest.policies.SetPolicyRuleState(policy_name, partial_rule_name,
                                                                                         state,
                                                                                         organization=organization)
                else:
                    state_status, state_response = self.rest.policies.SetPolicyRuleState(policy_name,
                                                                                         partial_rule_name,
                                                                                         state)
                if not state_status:
                    raise Exception(
                        f'Could not get response from the management when tried to change the action. \n{state_response}')

            if organization:
                rules_info = self.get_policy_info({'name': policy_name}, 'rules', organization=organization)[0]['rules']
            else:
                rules_info = self.get_policy_info({'name': policy_name}, 'rules')[0]['rules']
            filtered_rule = list(filter(lambda x: x['name'] == rule_name, rules_info))[0]

            # Validation
            if action:
                if filtered_rule['securityAction'] == action:
                    Reporter.report(f'Successfully changed the action of the rule {rule_name} to {action}')
                    return True
                else:
                    raise Exception(f'Could not change the action of the rule {rule_name} to {action}')

            if state:
                if (filtered_rule['enabled'] == 'true' and state == 'Enabled') or (
                        filtered_rule['enabled'] == 'false' and state == 'Disabled'):
                    Reporter.report(f'Successfully changed the state of the rule {rule_name} to {state}')
                    return True
                else:
                    raise Exception(f'Could not change the state of the rule {rule_name} to {state}')

        except Exception as e:
            assert False, str(e)

    def assign_policy(self, policy_name, group_name, timeout=60, organization=None):
        """
        :param timeout: time to wait for collector configuration to be uploaded
        :param policy_name: string, the name of the policy to assign,
        :param group_name: string or list, the name of the group that the policy will be assigned to.
        :return: True if succeeded, False if failed.
        """
        if organization:
            status, response = self.rest.policies.AssignCollector(policy_name, group_name, organization)
        else:
            status, response = self.rest.policies.AssignCollector(policy_name, group_name)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f"Assigned the policy {policy_name} to the group {group_name} successfully")
        sleep(timeout)
        return True

    def clone_policy(self, old_policy, new_policy):
        """
        Clone policy
        :param oldPolicy: name of the old policy to clone
        :param newPolicy: name of the new policy
        :return:
        """
        status, response = self.rest.policies.ClonePolicy(old_policy, new_policy)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Cloned policy ' + old_policy + 'to policy: ' + new_policy + ' successfully.')
        return True

    def get_exceptions(self, eventId=None):
        """
        :param eventId: string, optional, if no event id given returns all the exceptions
        :return: dictionary or list of dictionaries (if no event id given) with the following parameters:
                    exceptionId, originEventId, userName, updatedAt, createdAt, comment, selectedDestinations,
                    optionalDestinations, selectedCollectorGroups, optionalCollectorGroups, alerts.
        """
        if eventId:
            status, response = self.rest.exceptions.GetEventExceptions(eventId)
        else:
            status, response = self.rest.exceptions.ListExceptions()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if eventId:
            exceptions = loads(response.text)[0]
        else:
            exceptions = loads(response.text)

        Reporter.report(f'Successfully got information of the following event id: {eventId}.')
        return exceptions

    def delete_exception(self, exceptionId):
        """
        :param exceptionId: string.
        """
        status, response = self.rest.exceptions.DeleteException(exceptionId)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Deleted the exception of the event: {exceptionId} successfully.')
        return True

    def delete_all_exceptions(self):
        """
        :return: True if succeeded deleting all the events, False otherwise.
        """
        exceptions = self.get_exceptions()

        if not exceptions:
            return False

        success = True
        for exception in exceptions:
            if not self.delete_exception(exception['exceptionId']):
                success = False

        Reporter.report('Successfully deleted all exceptions.')

        return success

    def get_playbook_info(self, validation_data=None, output_parameters=None, organization=None):
        """
        :param validation_data: string, the data about the wanted policy.
        :param output_parameters: string or list, the parameters to get from the given policy.
               parameter options: 'name', 'operationMode', 'agentGroups', 'rules'.
        :return: list of dictionaries, the information for the given data.
        """
        if organization:
            status, response = self.rest.playbooks.ListPolicies(organization=organization)
        else:
            status, response = self.rest.playbooks.ListPolicies()
        return self._get_info(status, response, validation_data, output_parameters)

    """ *********************************************** CommCtrl ************************************************ """

    def set_application_mode(self, vendors, policy_names, decision, kwargs):
        """
        :param vendors: list of strings
        :param policy_names: List of policy names
        :param decision: 'Allow' or 'Deny'
        :param kwargs: optional parameters:
                        products: can be string ot list of strings
                        versions: can be string ot list of strings
                        organization: string
                        signed: 'True' or 'False'
                        applyNested: 'True' or 'False'
        :return: True/False
        """
        kwargs['policies'] = policy_names
        kwargs['decision'] = decision
        kwargs['vendors'] = vendors
        status, response = self.rest.commControl.SetApplicationMode(**kwargs)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully set application mode to {kwargs["decision"]}')
        return True

    def create_policy(self, policy_name, default_decision, collector_groups, comment):

        status, response = self.rest.commControl.CreatePolicy(policy_name, default_decision, collector_groups, comment)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report('Created policy ' + policy_name + ' successfully.')
        return True

    def set_policy_mode_comm_control(self, policy_names, mode):

        status, response = self.rest.commControl.SetPolicyMode(policy_names, mode)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully got information of all commcontrol products')
        return True

    def assign_collector_to_policy_comm_control(self, collector_groups, policy, organization=None):
        """
        :param collector_groups: String or list
        :return:
        """
        status, response = self.rest.commControl.AssignCollectorToPolicy(collector_groups, policy, organization)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Assigned collectors {collector_groups} to policy {policy} successfully')
        return True

    def get_commcontrol_product_list(self):
        status, response = self.rest.commControl.ListProducts()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        commcontrols = loads(response.text)

        Reporter.report(f'Successfully got information of all commcontrol products')
        return commcontrols

    """ ********************************************* Organization ********************************************** """

    def get_organizations(self):
        status, response = self.rest.organizations.ListOrganizations()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        organizations = loads(response.text)

        Reporter.report(f'Successfully got information of all organizations')
        return organizations

    def export_organization(self, organization, destination_name, zip_file_path):
        status, response = self.rest.organizations.ExportOrganization(organization, destination_name)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        export_file = open(zip_file_path, 'wb')
        export_file.write(response.content)
        export_file.close()

        Reporter.report(f'Organization {organization} was exported to {destination_name} successfully')
        return True

    def import_organization(self, import_file_path):

        status, response = self.rest.organizations.ImportOrganization(import_file_path)
        if not status:
            assert False, f'Could not get response from the management \n{response.text}'

        Reporter.report(f'Organization was imported from file {import_file_path} successfully')
        return loads(response.text)['verificationCode']

    def transfer_collectors(self, verification_code, source_organization, target_organization, sourceAggregatorId,
                            targetAggregatorDestination, targetAggregatorPort=8081,
                            ignore_aggregator_connection_test=False):
        aggregators_map = [
            {"sourceAggregatorId": sourceAggregatorId, "targetAggregatorDestination": targetAggregatorDestination,
             "targetAggregatorPort": targetAggregatorPort}]
        status, response = self.rest.organizations.TransferCollectors(verification_code, source_organization,
                                                                      target_organization,
                                                                      aggregators_map,
                                                                      ignore_aggregator_connection_test)

        if not status:
            assert False, f'Could not get response from the management \n{response}'

        Reporter.report(f'Collectors transferred successfully')
        return True

    def transfer_collectors_abort(self, organization):
        status, response = self.rest.passthrough.ExecuteRequest(url='/organizations/abort-migration',
                                                                mode='put', inputParams={"organization": organization})
        if not status:
            assert False, f'Could not get response from the management \n{response}'

        Reporter.report(f'Abort migration successfully')
        return True

    def transfer_collectors_stop(self, source_organization):
        status, response = self.rest.organizations.TransferCollectorsStop(source_organization)

        if not status:
            assert False, f'Could not get response from the management \n{response}'

        Reporter.report(f'Transfer collectors stopped successfully')
        return True

    """ ************************************************ Users ************************************************* """

    def get_users(self, organization):
        status, response = self.rest.users.ListUsers(organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        users = loads(response.text)

        Reporter.report(f'Successfully got information of all users')
        return users

    def create_user(self, username, password, firstName, lastName, email, roles, organization=None):
        url = "/users/create-user"
        inputParams = {}
        bodyParams = {"username": username,
                      "password": password,
                      "confirmPassword": password,
                      "firstName": firstName,
                      "lastName": lastName,
                      "email": email,
                      "roles": roles}
        if organization:
            inputParams["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=inputParams,
                                                                body=bodyParams)
        if status:
            Reporter.report(f"user {username} created successfully")
            return True
        else:
            Reporter.report(f"failed to create user {username}, response: {response}")
            return False

    def delete_user(self, username, organization=None):
        status, response = self.rest.users.DeleteUser(username, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully delete user: {username}')
        return status

    def reset_password(self, username, password, organization=None):
        status, response = self.rest.users.ResetPassword(username, password, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully reset password for user: {username}')
        return status

    def update_user(self, username, firstName, lastName, email, roles, organization=None):
        url = "/users/update-user"

        inputParams = {"username": username}

        bodyParams = {"username": username,
                      "firstName": firstName,
                      "lastName": lastName,
                      "email": email,
                      "roles": roles}
        if organization:
            inputParams["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=inputParams,
                                                                body=bodyParams)
        if status:
            Reporter.report(f"user {username} updated successfully")
            return True
        else:
            Reporter.report(f"failed to update user {username}, response: {response}")
            return False

    """ ************************************************ IpSets ************************************************* """

    def create_ipSet(self, name, include=None, exclude=None, organization=None, description=None):
        """

        :param name:
        :param include: must be a list
        :param exclude: must be a list
        :param organization:
        :param description:
        :return:
        """
        status, response = self.rest.ipsets.CreateIpSet(name, include, exclude, organization, description)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully created ipSet {name}')
        return status

    def delete_ipSet(self, ipSets, organization=None):
        status, response = self.rest.ipsets.DeleteIpSet(ipSets, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully deleted ipSet {ipSets}')
        return status

    def update_ipSet(self, name, include=None, exclude=None, organization=None, description=None):
        """

        :param name:
        :param include: must be a list
        :param exclude: must be a list
        :param organization:
        :param description:
        :return:
        """
        status, response = self.rest.ipsets.UpdateIpSet(name, include, exclude, organization, description)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully deleted ipSet {name}')
        return status

    def get_ipsets(self, ip=None, organizaion=None):
        if organizaion is None:
            status, response = self.rest.ipsets.ListIpSets(ip)
        else:
            status, response = self.rest.ipsets.ListIpSets(ip, organizaion)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        ipsets = loads(response.text)

        Reporter.report(f'Successfully got information of all ipsets')
        return ipsets

    """ *********************************************** Playbooks ************************************************ """

    def clone_playbook(self, source_policy_name, new_policy_name, organization=None):
        status, response = self.rest.playbooks.ClonePolicy(source_policy_name, new_policy_name, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully clone playbook {source_policy_name} to {new_policy_name}')
        return True

    def playbook_assign_collector_group(self, collector_group_names, policy_name, organization=None):
        status, response = self.rest.playbooks.AssignCollectorGroup(collector_group_names, policy_name, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully assign collector group {policy_name} to {collector_group_names}')
        return True

    def playbook_set_mode_prevention(self, policy_name, organization=None):
        status, response = self.rest.playbooks.SetModePrevention(policy_name, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully set {policy_name} mode to prevention')
        return True

    def playbook_set_mode_simulation(self, policy_name, organization=None):
        status, response = self.rest.playbooks.SetModeSimulation(policy_name, organization)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully set {policy_name} mode to simulation')

        return True

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

    def _get_values(self, name, ip, raw_data):
        """
        format for get value functions.
        :param name: str, name of the component.
        :param ip: str, the ip address of the component.
        :param raw_data: list of dictionaries, raw data from the get component info functions.
        :return: if there was one component given -> str, the value.
                 if there were more then one components given -> dictionary, matches each ip/name to its value.
                 if failed -> false
        """
        if not raw_data:
            assert False, 'Could not get components value.'

        # making sure the data is list
        if isinstance(name, str):
            name = [name]
        if isinstance(ip, str):
            ip = [ip]

        # set data to the not-None parameter, if both not-None so data is ip, if both None data is None.
        data = ip or name

        # filtering the raw data using the data
        if data:
            filtered_data = list(filter(lambda x: list(x.values())[1] in data, raw_data))
        else:
            filtered_data = raw_data

        if not filtered_data:
            assert False, f'Not found the given component name: {name} or ip: {data} in the management.'

        return_dict = {}
        for component in filtered_data:
            values = list(component.values())
            return_dict[values[1]] = values[0]

        Reporter.report(f'Successfully got the data: {return_dict} of the component: {data}')

        if len(return_dict) == 1:
            return list(return_dict.values())[0]

        return return_dict

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
                    assert False,f'Could not get the information, the given parameter: {parameter} does not exist. The options are: {list(component.keys())}'

        if component_dict:
            return_list.append(component_dict)

        if return_list:
            return return_list

        else:
            assert False, f'Could not get the information: {raw_data} based on the given parameters: {parameters}.'


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


    def _translate_dictionary(self, dictionary, translate_dictionary):
        """

        :param dictionary:
        :return:
        """
        for k, v in translate_dictionary.items():
            value = dictionary.pop(k, False)
            if value:
                dictionary[v] = value
        return dictionary


    def _translate_list_of_dictionaries(self, data, translate_dictionary):
        return_list = []
        for dictionary in data:
            return_list.append(self._translate_dictionary(dictionary, translate_dictionary))

        return return_list


    def isolate_devices(self, list_devices_names):
        url = "/inventory/isolate-collectors"
        params = {'devices': list_devices_names}
        response = self.rest.passthrough.ExecuteRequest(url, mode='put', inputParams=params)
        if response[1].status_code != 200:
            assert False, f"failed to isolate devices: {list_devices_names}"
        else:
            Reporter.report(f"succeed to isolate devices: {list_devices_names}")
            return True


    def unisolate_devices(self, list_devices_names):
        url = "/inventory/unisolate-collectors"
        params = {'devices': list_devices_names}
        response = self.rest.passthrough.ExecuteRequest(url, mode='put', inputParams=params)
        if response[1].status_code != 200:
            assert False, f"failed to unisolate devices: {list_devices_names}"
        else:
            Reporter.report(f"succeed to unisolate devices: {list_devices_names}")
            return True


    """ ********************************************* remediation ************************************************ """


    def remediate_device(self, device, process_id=None, files_to_delete=None, organization=None, **kwargs):
        status, response = self.rest.forensics.RemediateDevice(device, process_id, files_to_delete, organization,
                                                               **kwargs)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully remediate device: {device}')
        return status


    def kill_process(self, device, process_id, organization=None, **kwargs):
        status, response = self.rest.forensics.KillProcess(device, process_id, organization, **kwargs)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully killed process: {process_id}')
        return status


    def delete_file(self, device, files_to_delete, organization=None, **kwargs):
        status, response = self.rest.forensics.DeleteFile(device, files_to_delete, organization, **kwargs)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully deleted files: {files_to_delete}')
        return status


    def search_hash(self, hashes):
        status, response = self.rest.forensics.SearchHash(hashes)
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Successfully searched hashes: {hashes}')
        return status


    def delete_exception_by_event_name(self, eventName):
        urlDelete = "/exceptions/delete"
        urlget = "/exceptions/list-exceptions"
        response = self.rest.passthrough.ExecuteRequest(urlget, mode='get', inputParams=None)[1].text
        exceptionList = json.loads(response)
        exceptionsIds = []
        for item in exceptionList:
            try:
                name = item["alerts"][0]["process"]["name"]
                if eventName in str(name):
                    exceptionsIds.append(item["exceptionId"])
            except:
                pass
        for exceptionID in exceptionsIds:
            params = {'exceptionId': exceptionID}
            response = self.rest.passthrough.ExecuteRequest(urlDelete, mode='delete', inputParams=params)
            if response[1].status_code != 200:
                assert False, f"delete exception failed, exceptionID: {exceptionID}, response: {response}"
            else:
                Reporter.report(f'exceptionID {exceptionID} deleted successfully!')
        return True


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


    def update_organization(self, organization, expirationDate, serversAllocated, workstationsAllocated, iotAllocated):
        url = "/organizations/update-organization"
        body = {"expirationDate": expirationDate, "name": organization, "serversAllocated": serversAllocated,
                "workstationsAllocated": workstationsAllocated, "iotAllocated": iotAllocated}
        input = {"organization": organization}
        response = self.rest.passthrough.ExecuteRequest(url, mode='put', inputParams=input, body=body)
        if response[1].status_code != 200:
            assert False, f"update organization failed, organization: {organization}, response: {response}"
        else:
            Reporter.report(f'organization {organization} updated successfully!')
        return True


    def create_organization(self, expirationDate, organization, reg_pass, serversAllocated, workstationsAllocated,
                            iotAllocated):
        url = "/organizations/create-organization"
        body = {"expirationDate": expirationDate,
                "name": organization,
                "password": reg_pass,
                "passwordConfirmation": reg_pass,
                "serversAllocated": serversAllocated,
                "workstationsAllocated": workstationsAllocated,
                "iotAllocated": iotAllocated}
        response = self.rest.passthrough.ExecuteRequest(url, mode='post', body=body, inputParams=[])
        if response[1].status_code != 200:
            assert False, f"create organization failed, organization: {organization}, response: {response}"
        else:
            Reporter.report(f'organization {organization} created successfully!')
        return True


    def delete_organization_collectors(self, organization):
        url = "/inventory/list-collectors"
        inputParams = {"organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get",
                                                                inputParams=inputParams)
        collectorsList = ast.literal_eval(response.text)
        for collector in collectorsList:
            url = "/inventory/delete-collectors"
            status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="delete",
                                                                    inputParams={"devicesIds": collector["id"],
                                                                                 "organization": organization})


    def delete_organizations_and_organization_collectors(self, organizations):
        for organization in organizations:
            try:
                self.delete_organization_collectors(organization)
                url = "/organizations/delete-organization"
                inputParams = {"organization": organization}
                status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="delete", inputParams=inputParams)
            except:
                pass
        return True


    def create_iot_groups(self, name, organization=None):
        params = {"name": name}
        if organization:
            params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/iot/create-iot-group", mode="post",
                                                                inputParams=params)
        if status:
            return loads(response.text)
        return False


    def list_of_iot_devices(self, **kwargs):
        status, response = self.rest.passthrough.ExecuteRequest(url="/iot/list-iot-devices", mode="get",
                                                                inputParams=kwargs)
        if status:
            return loads(response.text)
        return False


    def list_of_iot_groups(self, organization="Default"):
        status, response = self.rest.passthrough.ExecuteRequest(url="/iot/list-iot-groups", mode="get",
                                                                inputParams={"organization": organization})
        if status:
            return loads(response.text)
        return False


    def move_iot_devices(self, iotDevices, targetIotGroup, organization=None):
        params = {}
        params["iotDevices"] = iotDevices
        params["targetIotGroup"] = targetIotGroup
        if organization:
            params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/iot/move-iot-devices", mode="pot",
                                                                inputParams=params)
        if status:
            return True
        return False


    def iot_fast_scan(self, **kwargs):
        status, response = self.rest.passthrough.ExecuteRequest(url="/inventory/fast-iot-scan", mode="put",
                                                                inputParams=kwargs)
        if status:
            return True
        return False


    def validate_iot_device(self, ip, model, type):
        devices = self.list_of_iot_devices()
        spesific_device = None
        for device in devices:
            if device['internalIp'] == ip:
                spesific_device = device
        if spesific_device['model'] == model and spesific_device['type'] == type:
            return True
        else:
            return False


    def set_device_control_policy(self, mode):
        """
        :param mode: Prevention or Simulation.
        :return: True or False.
        """
        return self.set_policy_mode("Device Control", mode)


    def edr2_search(self, **kwargs):
        body = {
            "category": "All",
            "devices": [],
            "facets": [],
            "filters": [],
            "itemsPerPage": 20,
            "offset": 0,
            "query": "",
            "time": "lastHour",
            "sorting": []
        }
        body.update(kwargs)
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/search", mode="post",
                                                                inputParams={},
                                                                body=body)
        json_data = json.loads(response.text)
        return json_data


    def edr2_count(self, **kwargs):
        body = {
            "category": "All",
            "devices": [],
            "facets": [],
            "filters": [],
            "itemsPerPage": 20,
            "offset": 0,
            "query": "",
            "time": "lastHour",
            "sorting": []
        }
        body.update(kwargs)
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/counts", mode="post",
                                                                inputParams={},
                                                                body=body)
        json_data = json.loads(response.text)
        return json_data


    def edr2_device_list(self, **kwargs):
        body = {
            "category": "All",
            "devices": [],
            "facets": [],
            "filters": [],
            "itemsPerPage": 20,
            "offset": 0,
            "time": "lastHour",
            "query": "",
            "sorting": []
        }
        body.update(kwargs)
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/device-list", mode="post",
                                                                inputParams={},
                                                                body=body)
        json_data = json.loads(response.text)
        return json_data


    def edr2_facets(self, **kwargs):
        body = {
            "category": "All",
            "devices": [],
            "facets": [],
            "filters": [],
            "itemsPerPage": 20,
            "offset": 0,
            "query": "",
            "sorting": []
        }
        body.update(kwargs)
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/facets", mode="post",
                                                                inputParams={},
                                                                body=body)
        json_data = json.loads(response.text)
        return json_data


    def edr2_schema(self):
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/schema", mode="get",
                                                                inputParams={})
        json_data = json.loads(response.text)
        return json_data


    def get_collectors_list(self, ips, organization=None):
        url = "/inventory/list-collectors"
        inputParams = {"ips": ips, "organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams=inputParams)
        if status:
            Reporter.report(f"collectors-info {response.text}")
            collectorsList = ast.literal_eval(response.text)
            return collectorsList
        else:
            assert False, f"failed to get collectors info, response: {response}"


    def create_update_exclusion(self, action, exclusionListName, exclude_name, exclusion_type, value, organization,
                                enabled, eventTypes, operatingSystems, secondaryValue=None, exclusionId=None,
                                comments=""):
        """
          create exclusion
          :param action: create or update
          :param exclusionListName: exclusion list name.
          :param exclude_name: exclude name
          :param exclusion_type: Source/Target
          :param value: string
          :param organization: organization name
          :param enabled: True or False
          :param eventTypes: list of events types
          :param operatingSystems: list of os systems
          :param secondaryValue: optional. additional values
          :param exclusionId: for update. exclusion id
          :param comments: exclusion description
          :return: True or False.
          """

        exclusion = [
            {
                "attributes": [{
                    "name": exclude_name,
                    "type": exclusion_type,
                    "value": value,
                    "secondaryValue": secondaryValue,
                    "comments": comments}],
                "enabled": enabled,
                "eventTypes": eventTypes,
                "operatingSystems": operatingSystems
            }
        ]

        if action == "create":
            mode = "post"
        elif action == "update":
            mode = "put"
            exclusion[0]["exclusionId"] = exclusionId
        url = "/exclusions/exclusion"
        body = {"exclusionListName": exclusionListName, "exclusions": exclusion, "organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode=mode, inputParams={}, body=body)
        if status:
            return True
        else:
            assert False, f"failed to create exclusion, error: {response}"


    def delete_exclusion(self, exclusionIds, organization):
        """
          create exlusion
          :param exclusionIds: list of exclusion ids
          :param organization: organization name
          :return: True or False.
          """
        url = "/exclusions/exclusion"
        body = {"exclusionIds": exclusionIds, "organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="delete", inputParams={}, body=body)
        if status:
            return True
        else:
            assert False, f"failed to delete exclusion, error: {response}"


    def get_exclusions_list(self, organization):
        url = "/exclusions/exclusions-list"
        input_params = {"organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams=input_params)
        if status:
            exclusions = yaml.load(str(response.text))
            return exclusions
        else:
            assert False, f"failed to get exclusion list, error: {response}"


    def create_exclusion_list(self, name, collectorGroupIds, organization):
        url = "/exclusions/exclusions-list"
        body_params = {"name": name, "collectorGroupIds": collectorGroupIds, "organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams={}, body=body_params)
        if status:
            return True
        else:
            assert False, f"failed to create exclusion list, error: {response}"


    def update_exclusion_list(self, listName, collectorGroupIds, organization, newName=None):
        url = "/exclusions/exclusions-list"
        body_params = {"listName": listName, "collectorGroupIds": collectorGroupIds, "organization": organization}
        if newName:
            body_params["newName"] = newName
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="put", inputParams={}, body=body_params)
        if status:
            return True
        else:
            assert False, f"failed to update exclusion list, error: {response}"


    def delete_exclusion_list(self, name, organization):
        url = "/exclusions/exclusions-list"
        input_params = {"listName": name, "organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="delete", inputParams=input_params)
        if status:
            return True
        else:
            assert False, f"failed to delete exclusion list, error: {response}"


    def exclusion_metadata(self):
        url = "/exclusions/exclusions-metadata"
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams={})
        if status:
            exclusions = yaml.load(str(response.text))
            return exclusions
        else:
            assert False, f"failed to get meta data, error: {response}"


    def get_threat_hunting_metadata(self):
        url = "/threat-hunting-settings/threat-hunting-metadata"
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams={})
        if status:
            result = yaml.load(str(response.text))
            return result
        else:
            assert False, f"failed to get meta data, error: {response}"


    def get_threat_hunting_profiles_list(self, organization):
        url = "/threat-hunting-settings/threat-hunting-profile"
        input_params = {"organization": organization}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="get", inputParams=input_params)
        if status:
            result = yaml.load(str(response.text))
            return result
        else:
            assert False, f"failed to get meta data, error: {response}"


    def update_threat_hunting_profile(self, associatedCollectorGroupIds, name, enabled, eventTypes, category_name,
                                      organization, newName=None):
        url = "/threat-hunting-settings/threat-hunting-profile"
        threatHuntingCategoryList = [{"enabled": enabled, "eventTypes": eventTypes, "name": category_name}]
        body = {"organization": organization, "name": name, "associatedCollectorGroupIds": associatedCollectorGroupIds,
                "threatHuntingCategoryList": threatHuntingCategoryList}
        if newName:
            body["newName"] = newName
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams={}, body=body)
        if status:
            result = yaml.load(str(response.text))
            return result
        else:
            assert False, f"failed to update threat hunting profile, error: {response}"


    def delete_threat_hunting_profile(self, name, organization):
        url = "/threat-hunting-settings/threat-hunting-profile"
        input_params = {"organization": organization, "name": name}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="delete", inputParams=input_params)
        if status:
            return True
        else:
            assert False, f"failed to delete threat hunting profile, error: {response}"


    def clone_threat_hunting_profile(self, existingProfileName, cloneProfileName, organization):
        url = "/threat-hunting-settings/threat-hunting-profile-clone"
        input_params = {"organization": organization, "existingProfileName": existingProfileName,
                        "cloneProfileName": cloneProfileName}
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=input_params)
        if status:
            result = yaml.load(str(response.text))
            return result
        else:
            assert False, f"failed to clone threat hunting profile, error: {response}"


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


    def unarchive_events(self, ids, organization=None):
        input_params = {"eventIds": ids, "archived": True}
        if organization:
            input_params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/events", mode="put",
                                                                body={"archive": False},
                                                                inputParams=input_params)
        if status:
            return True
        else:
            assert False, f"failed to unarchive events, response: {response}"


    def archive_events(self, ids, organization=None):
        input_params = {"eventIds": ids, "archived": False}
        if organization:
            input_params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/events", mode="put",
                                                                body={"archive": True},
                                                                inputParams=input_params)
        if status:
            return True
        else:
            assert False, f"failed to unarchive events, response: {response}"


    def edr2_create_or_edit_tag(self, newTagName, tagId=None, tagName=None):
        body = {}
        body["newTagName"] = newTagName
        if tagId:
            body["tagId"] = tagId
        if tagName:
            body["tagName"] = tagName
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/create-or-edit-tag", mode="post",
                                                                body=body,
                                                                inputParams={})
        if status:
            return True
        else:
            assert False, f"failed to create or edit tag {tagName}, response: {response}"


    def edr2_save_query(self, name, time, **kwargs):
        input_params = {}
        kwargs["name"] = name
        kwargs["time"] = time
        id = kwargs.get("id", None)
        if id:
            input_params["id"] = kwargs["id"]
            del kwargs["id"]
        queryToEdit = kwargs.get("queryToEdit", None)
        if queryToEdit:
            input_params["queryToEdit"] = kwargs["queryToEdit"]
            del kwargs["queryToEdit"]
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/save-query", mode="post",
                                                                body=kwargs,
                                                                inputParams=input_params)
        if status:
            return True
        else:
            assert False, f"failed to save query, response: {response}"


    def edr2_delete_saved_queries(self, **kwargs):
        """
        :param kwargs: source, queryIds, queryNames, organization, scheduled, deleteFromCommunity, deleteAll
        :return: True or False.
        """

        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/delete-saved-queries",
                                                                mode="delete",
                                                                inputParams=kwargs)
        if status:
            return True
        else:
            assert False, f"failed to delete queries, response: {response}"


    def edr2_delete_tags(self, tagIds=None, tagNames=None, organization="All Organizations"):
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/delete-tags",
                                                                mode="delete",
                                                                inputParams={"tagIds": tagIds, "tagNames": tagNames,
                                                                             "organization": organization})
        if status:
            return True
        else:
            assert False, f"failed to delete tags, response: {response}"


    def edr2_list_tags(self, organization="All Organizations"):
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/list-tags",
                                                                mode="get",
                                                                inputParams={"organization": organization})
        if status:
            return ast.literal_eval(response.text)
        else:
            assert False, f"failed to get tags list, response: {response}"


    def edr2_list_saved_queries(self, organization="All Organizations"):
        status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/list-saved-queries",
                                                                mode="get",
                                                                inputParams={"organization": organization})
        if status:
            return json.loads(response.text)
        else:
            assert False, f"failed to get saved queries list, response: {response}"


    def assign_collector_group_to_threat_hunting_profile(self, profile_name, group_name, organization):
        groupid = None
        groups = self.get_collector_groups_info(organization=organization)
        for group in groups:
            if group_name == group["name"]:
                groupid = group["id"]
                break

        update_profile = None
        profiles = self.get_threat_hunting_profiles_list(organization)
        for profile in profiles:
            if profile["name"] == profile_name:
                update_profile = profile
                break
        update_profile['associatedCollectorGroupIds'] = [groupid]
        update_profile['organization'] = organization
        del update_profile['immutable']

        url = "/threat-hunting-settings/threat-hunting-profile"
        status, response = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams={},
                                                                body=update_profile)
        if status:
            result = yaml.load(str(response.text))
            return result
        else:
            assert False, f"failed to update threat hunting profile, error: {response}"


    def com_control_assign_collector_group(self, collectorGroupName, policyName, organization=None, forceAssign=None):
        params = {"collectorGroups": [collectorGroupName], "policyName": policyName}
        if organization:
            params["organization"] = organization
        if forceAssign:
            params["forceAssign"] = forceAssign
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/assign-collector-group",
                                                                mode="put",
                                                                inputParams=params)
        if status:
            return True
        else:
            assert False, f"failed to assign collector group {collectorGroupName} to policy {policyName}"


    def com_control_clone_policy(self, sourcePolicyName, newPolicyName, organization=None):
        params = {"sourcePolicyName": sourcePolicyName, "newPolicyName": newPolicyName}
        if organization:
            params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/clone-policy",
                                                                mode="post",
                                                                inputParams=params)
        if status:
            return True
        else:
            assert False, f"failed to clone policy {sourcePolicyName} to policy {newPolicyName}"


    def com_control_get_list_policies(self, **kwrags):
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/list-policies",
                                                                mode="get",
                                                                inputParams=kwrags)
        if status:
            return json.loads(response.text)
        else:
            assert False, f"failed to get list policies"


    def com_control_get_list_products(self, **kwrags):
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/list-products",
                                                                mode="get",
                                                                inputParams=kwrags)
        if status:
            return json.loads(response.text)
        else:
            assert False, f"failed to get list policies"


    def com_control_update_vendor_policy_rule_association(self, policyName, vendorName, signed, excluded,
                                                          organization=None):
        params = {"policyName": policyName, "vendorName": vendorName, "signed": signed, "excluded": excluded}
        if organization:
            params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(
            url="/comm-control/update-vendor-policy-rule-association",
            mode="put",
            inputParams=params)
        if status:
            return True
        else:
            assert False, f"failed to update vendor policy rule"


    def com_control_set_policy_rule_state(self, policyName, ruleName, state, organization=None):
        params = {"policyName": policyName, "ruleName": ruleName, "state": state}
        if organization:
            params["organization"] = organization
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/set-policy-rule-state",
                                                                mode="put",
                                                                inputParams=params)
        if status:
            return True
        else:
            assert False, f"failed to set policy rule state"


    def com_control_set_policy_permission(self, policies, decision, **kwargs):
        kwargs["policies"] = [policies]
        kwargs["decision"] = decision
        status, response = self.rest.passthrough.ExecuteRequest(url="/comm-control/set-policy-permission",
                                                                mode="put",
                                                                inputParams=kwargs)
        if status:
            return True
        else:
            assert False, f"failed to set policy rule state"


    def get_exceptions_by_parameters(self, **kwargs):
        status, response = self.rest.passthrough.ExecuteRequest(url="/exceptions/list-exceptions",
                                                                mode="get",
                                                                inputParams=kwargs)
        if status:
            return loads(response.text)
        else:
            assert False, f"failed to get exceptions"
