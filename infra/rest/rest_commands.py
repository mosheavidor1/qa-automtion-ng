from ensilo.platform.rest.nslo_management_rest import NsloManagementConnection, NsloRest
from infra.rest.administrator_rest import AdministratorRest
from infra.rest.communication_control_rest import CommunicationControlRest
from infra.rest.events_rest import EventsRest
from infra.rest.exceptions_rest import ExceptionsRest
from infra.rest.exclusions_rest import ExclusionsRest
from infra.rest.forensics_rest import ForensicsRest
from infra.rest.hash_rest import HashRest
from infra.rest.integrations_rest import IntegrationRest
from infra.rest.iot_rest import IoTRest
from infra.rest.ip_sets_rest import IpSetsRest
from infra.rest.organizations_rest import OrganizationsRest
from infra.rest.playbooks_rest import PlaybooksRest
from infra.rest.policies_rest import PoliciesRest
from infra.rest.system_events_rest import SystemEventsRest
from infra.rest.system_inventory_rest import SystemInventoryRest
from infra.rest.threat_hunting_rest import ThreatHuntingRest
from infra.rest.threat_hunting_settings_rest import ThreatHuntingSettingsRest
from infra.rest.users_rest import UsersRest


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
        self.administrator = AdministratorRest(nslo_rest=self.rest)
        self.communication_control = CommunicationControlRest(nslo_rest=self.rest)
        self.events = EventsRest(nslo_rest=self.rest)
        self.exceptions = ExceptionsRest(nslo_rest=self.rest)
        self.exclusions = ExclusionsRest(nslo_rest=self.rest)
        self.forensics = ForensicsRest(nslo_rest=self.rest)
        self.hash = HashRest(nslo_rest=self.rest)
        self.integration = IntegrationRest(nslo_rest=self.rest)
        self.iot = IoTRest(nslo_rest=self.rest)
        self.ip_sets = IpSetsRest(nslo_rest=self.rest)
        self.organizations = OrganizationsRest(nslo_rest=self.rest)
        self.playbooks = PlaybooksRest(nslo_rest=self.rest)
        self.policies = PoliciesRest(nslo_rest=self.rest)
        self.system_events = SystemEventsRest(nslo_rest=self.rest)
        self.system_inventory = SystemInventoryRest(nslo_rest=self.rest)
        self.threat_hunting = ThreatHuntingRest(nslo_rest=self.rest)
        self.threat_hunting_settings = ThreatHuntingSettingsRest(nslo_rest=self.rest)
        self.users_rest = UsersRest(nslo_rest=self.rest)

    # def get_collector_info(self, validation_data=None, output_parameters=None, organization=None):
    #     """
    #     :param output_parameters: string or list, the information parameter to get from the given collector.
    #                               options for collector parameters: 'id', 'name', 'collectorGroupName', 'operatingSystem',
    #                                                          'ipAddress' (0.0.0.0), 'osFamily', 'state', 'lastSeenTime',
    #                                                           'version', 'macAddresses', 'loggedUsers'
    #     :param validation_data: dictionary, the data to get from the collector.
    #     :return: according to the get_info function.
    #     """
    #     status, response = self.rest.inventory.ListCollectors(organization=organization)
    #     return self._get_info(status, response, 'collector', validation_data, output_parameters)
    #
    # def get_aggregator_info(self, validation_data=None, output_parameters=None):
    #     """
    #     :param output_parameters: string or list, the information parameter to get from the given core.
    #                               options for collector parameters: 'id', 'hostName', 'ipAddress', 'version',
    #                               'numOfAgents', 'numOfDownAgents', 'state'.
    #     :param validation_data: dictionary, the data to get from the core.
    #     :return: according to the get_info function.
    #     """
    #     status, response = self.rest.inventory.ListAggregators()
    #     return self._get_info(status, response, 'aggregator', validation_data, output_parameters)
    #
    # def get_core_info(self, validation_data=None, output_parameters=None):
    #     """
    #     :param output_parameters: string or list, the information parameter to get from the given core.
    #                               options for collector parameters: ['deploymentMode', 'ip' ('0.0.0.0:555'), 'name',
    #                               'version', 'status']
    #     :param validation_data: dictionary, the data to get from the core.
    #     :return: according to the get_info function.
    #     """
    #     status, response = self.rest.inventory.ListCores()
    #     return self._get_info(status, response, 'core', validation_data, output_parameters)
    #
    # def get_system_summery(self, parameter=None, log=False):
    #     """
    #     :param parameter: string or list, the information parameter to get from the system summery.
    #     :param log: boolean, True to log the full system summery.
    #     :return: string, the information for the given parameter.
    #     """
    #     if isinstance(parameter, str):
    #         parameter = [parameter]
    #
    #     status, response = self.rest.admin.GetSystemSummary()
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     summery = loads(response.text)
    #
    #     if parameter:
    #         summery = self._filter_data([summery], parameter)
    #         if summery:
    #             return summery[0]
    #
    #     return summery
    #
    # def set_system_mode(self, prevention: bool):
    #     """
    #     :param prevention: boolean, True for prevention mode or False for simulation.
    #     """
    #     if prevention:
    #         status, response = self.rest.admin.SetSystemModePrevention()
    #     else:
    #         status, response = self.rest.admin.SetSystemModeSimulation()
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #     else:
    #         Reporter.report(f'Successfully changed system mode')
    #         return True
    #
    # def create_group(self, name, organization=None):
    #     """
    #     :param name: string, the name of the group.
    #     :return: True if succeeded creating the group, False if failed.
    #     """
    #     group_status, group_response = self.rest.inventory.ListCollectorGroups(organization=organization)
    #     groups_list = self._get_info(group_status, group_response)
    #
    #     for group in groups_list:
    #         if name == group["name"]:
    #             Reporter.report('group ' + name + ' already exist')
    #             return True
    #
    #     status, response = self.rest.inventory.CreateCollectorGroup(name, organization)
    #
    #     group_status, group_response = self.rest.inventory.ListCollectorGroups(organization=organization)
    #     groups_list = self._get_info(group_status, group_response)
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     result = False
    #     for group in groups_list:
    #         if name in group["name"]:
    #             result = True
    #     assert result
    #
    #     Reporter.report('Created the group ' + name + ' successfully.')
    #     return True
    #
    # @allure.step("Move collectors {collectors_names} to group: {target_group_name} in organization: {target_organization}")
    # def move_collectors(self,
    #                     collectors_names: List[str],
    #                     target_group_name: str = "Default Collector Group",
    #                     current_collectors_organization: str = "Default",
    #                     target_organization: str = "Default",
    #                     expected_status_code: int = 200):
    #
    #     collectors_to_move = [fr'{current_collectors_organization}\{collector_name}' for collector_name in collectors_names]
    #     target_collector_group = fr'{target_organization}\{target_group_name}'
    #     organization = None
    #     if target_organization != "Default":
    #         organization = 'All organizations'
    #
    #     status, response = self.rest.inventory.MoveCollectors(collectors=collectors_to_move,
    #                                                           group=target_collector_group,
    #                                                           organization=organization)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Move Collector - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # def move_collector(self, validation_data, group_name):
    #     """
    #     :param validation_data: dictionary, the data of the collector to be moved.
    #     :param group_name: string, the name of the group to move the collector to.
    #     :return: True if succeeded, False if failed.
    #     """
    #     collector_name = list(map(lambda x: list(x.values())[0], self.get_collector_info(validation_data, 'name')))
    #     status, response = self.rest.inventory.MoveCollectors(collector_name, group_name)
    #     collector_group = self.get_collector_info(validation_data, 'collectorGroupName')
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     if collector_group[0]["collectorGroupName"] != group_name:
    #         assert False, 'Could not move the collector ' + str(
    #             collector_name) + ' to the group ' + group_name + '.'
    #
    #     Reporter.report(
    #         'Moved the collector ' + str(collector_name) + ' to the group ' + group_name + ' successfully.')
    #     return True
    #
    # """ ************************************************ Events ************************************************ """
    #
    # @allure.step("Get security events")
    # def get_security_events(self,
    #                         validation_data,
    #                         timeout=60,
    #                         sleep_delay=2,
    #                         fail_on_no_events=True):
    #     """
    #     :param validation_data: dictionary of the data to get.
    #                             options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
    #                             fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
    #                             Action, rule, strictMode.
    #
    #     :return: list of dictionaries with the event info.
    #              if the request failed or there were no events found -> False
    #     """
    #
    #     start_time = time.time()
    #     is_found = False
    #     error_message = None
    #     events = []
    #     while time.time() - start_time < timeout and not is_found:
    #         try:
    #             status, response = self.rest.events.ListEvents(**validation_data)
    #             if not status:
    #                 error_message = f'Could not get response from the management. \n{response}'
    #
    #             events = loads(response.text)
    #             if not len(events):
    #                 error_message = 'No event with the given parameters found.'
    #                 time.sleep(sleep_delay)
    #             else:
    #                 is_found = True
    #                 Reporter.report(f'Successfully got information of {len(events)} events.')
    #
    #         except Exception as e:
    #             Reporter.report(f'{error_message}, trying again')
    #             time.sleep(sleep_delay)
    #
    #     if not is_found and fail_on_no_events:
    #         assert False, f"{error_message} after waiting {timeout} seconds"
    #
    #     return events
    #
    # def delete_event_by_name(self, eventName):
    #     urlget = "/events/list-events"
    #     response = self.rest.passthrough.ExecuteRequest(urlget, mode='get', inputParams=None)[1].text
    #     eventsList = json.loads(response)
    #     eventsIds = []
    #     for item in eventsList:
    #         try:
    #             name = item["process"]
    #             if eventName in str(name):
    #                 eventsIds.append(item["eventId"])
    #         except:
    #             pass
    #     if len(eventsIds):
    #         return self.delete_events(eventsIds)
    #     else:
    #         Reporter.report('There is no events to delete with the given name.')
    #         return False
    #
    # def delete_events(self, event_ids):
    #     """
    #     :param event_ids: list of strings or string.
    #     """
    #     status, response = self.rest.events.DeleteEvents(event_ids)
    #     event_info = self.get_security_events({'Event ID': event_ids})
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     if event_info:
    #         assert False, 'Could not delete the given events.'
    #
    #     Reporter.report('Deleted the given events successfully.')
    #     return True
    #
    # @allure.step("Delete all events")
    # def delete_all_events(self, timeout=60):
    #     event_ids = []
    #     response = self.rest.events.ListEvents()
    #     as_list_of_dicts = json.loads(response[1].text)
    #     for single_event in as_list_of_dicts:
    #         event_id = single_event.get('eventId')
    #         event_ids.append(event_id)
    #
    #     if len(event_ids) > 0:
    #         self.rest.events.DeleteEvents(eventIds=event_ids)
    #         time.sleep(timeout)
    #
    #     else:
    #         Reporter.report("No events, nothing to delete")
    #
    # """ ************************************************ Exceptions ************************************************ """
    #
    # def create_exception(self, eventId, groups=None, destinations=None, organization="Default", useAnyPath=None,
    #                      useInException=None, wildcardFiles=None, wildcardPaths=None, **kwargs):
    #     """
    #       create exception
    #       :param eventId: event id for create exception
    #       :param groups: list of string or None for all groups
    #       :param destinations: list of destinations or None for all destinations
    #       :param organization: string or none for all organizations
    #       :param useAnyPath: useAnyPath
    #       :param useInException: useInException
    #       :param wildcardFiles: wildcardFiles
    #       :param wildcardPaths: wildcardPaths
    #       :return: True or False.
    #       """
    #
    #     url = "/events/create-exception"
    #     kwargs["eventId"] = eventId
    #     if groups:
    #         kwargs["collectorGroups"] = groups
    #         kwargs["allCollectorGroups"] = False
    #     else:
    #         kwargs["allCollectorGroups"] = True
    #     if destinations:
    #         kwargs["destinations"] = destinations
    #         kwargs["allDestinations"] = False
    #     else:
    #         kwargs["allDestinations"] = True
    #     if organization:
    #         kwargs["organization"] = organization
    #         kwargs["allOrganizations"] = False
    #     else:
    #         kwargs["allOrganizations"] = True
    #
    #     body = {}
    #     if useAnyPath:
    #         body["useAnyPath"] = useAnyPath
    #     if useInException:
    #         body["useInException"] = useInException
    #     if wildcardFiles:
    #         body["wildcardFiles"] = wildcardFiles
    #     if wildcardPaths:
    #         body["wildcardPaths"] = wildcardPaths
    #
    #     response, status = self.rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=kwargs, body=body)
    #     if status:
    #         return True
    #     else:
    #         assert False, f"failed to create exception, error: {response}"
    #
    # def get_exceptions(self, event_id=None):
    #     """
    #     :param event_id: string, optional, if no event id given returns all the exceptions
    #     :return: list of dictionaries with the following parameters:
    #                 exceptionId, originEventId, userName, updatedAt, createdAt, comment, selectedDestinations,
    #                 optionalDestinations, selectedCollectorGroups, optionalCollectorGroups, alerts.
    #     """
    #     if event_id:
    #         status, response = self.rest.exceptions.GetEventExceptions(event_id)
    #     else:
    #         status, response = self.rest.exceptions.ListExceptions()
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     exceptions = loads(response.text)
    #
    #     Reporter.report(f'Successfully got information of the following event id: {event_id}.')
    #     return exceptions
    #
    # def delete_exception(self, exception_id):
    #     """
    #     :param exceptionId: string.
    #     """
    #     status, response = self.rest.exceptions.DeleteException(exception_id)
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     Reporter.report(f'Deleted the exception of the event: {exception_id} successfully.')
    #     return True
    #
    # @allure.step("Delete all exceptions")
    # def delete_all_exceptions(self, timeout=60):
    #     exception_ids = []
    #     response = self.rest.exceptions.ListExceptions()
    #     as_list_of_dicts = json.loads(response[1].text)
    #     for single_exception in as_list_of_dicts:
    #         event_id = single_exception.get('exceptionId')
    #         exception_ids.append(event_id)
    #
    #     if len(exception_ids) > 0:
    #         for exc_id in exception_ids:
    #             self.rest.exceptions.DeleteException(exceptionId=exc_id)
    #         time.sleep(timeout)
    #     else:
    #         Reporter.report("No execptions, nothing to delete")
    #
    # """ ************************************************ Policies ************************************************ """
    #
    # def get_policy_info(self, validation_data=None, output_parameters=None, organization=None):
    #     """
    #     :param validation_data: string, the data about the wanted policy.
    #     :param output_parameters: string or list, the parameters to get from the given policy.
    #            parameter options: 'name', 'operationMode', 'agentGroups', 'rules'.
    #     :return: list of dictionaries, the information for the given data.
    #     """
    #     if organization:
    #         status, response = self.rest.policies.ListPolicies(organization=organization)
    #     else:
    #         status, response = self.rest.policies.ListPolicies()
    #     return self._get_info(status, response, 'policy', validation_data, output_parameters)
    #
    # def set_policy_mode(self, name, mode, organization=None):
    #     """
    #     :param name: string, the policy name.
    #     :param mode: string, 'Prevention' or 'Simulation'.
    #     :return: True if succeeded, False if failed.
    #     """
    #     status, response = self.rest.policies.SetPolicyMode(name, mode, organization)
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #
    #     Reporter.report('Changed the policy ' + name + 'mode to: ' + mode + '.')
    #     return status
    #
    # def assign_policy(self, policy_name, group_name, timeout=60, organization=None):
    #     """
    #     :param timeout: time to wait for collector configuration to be uploaded
    #     :param policy_name: string, the name of the policy to assign,
    #     :param group_name: string or list, the name of the group that the policy will be assigned to.
    #     :return: True if succeeded, False if failed.
    #     """
    #     status, response = self.rest.policies.AssignCollector(policy_name, group_name, organization)
    #
    #     if not status:
    #         assert False, f'Could not get response from the management. \n{response}'
    #     Reporter.report(f"Assigned the policy {policy_name} to the group {group_name} successfully")
    #     time.sleep(timeout)
    #     return True
    #
    # @allure.step("Get specific organization data: {organization_name}")
    # def get_specific_organization_data(self,
    #                                    organization_name: str) -> dict | None:
    #     all_orgs = self.get_all_organizations(expected_status_code=200)
    #     for single_org in all_orgs:
    #         if single_org.get('name') == organization_name:
    #             Reporter.attach_str_as_file(file_name='organization data',
    #                                         file_content=json.dumps(single_org,
    #                                                                 indent=4))
    #             return single_org
    #
    #     return None
    #
    # @allure.step("Get all organizations")
    # def get_all_organizations(self, expected_status_code: int = 200) -> List[dict]:
    #     status, response = self.rest.organizations.ListOrganizations()
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"List organizations - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    #     as_dict = json.loads(response.content)
    #     return as_dict
    #
    # @allure.step("Create organization")
    # def create_organization(self,
    #                         organization_data: CreateOrganizationRestData,
    #                         expected_status_code: int = 200):
    #
    #     data = json.loads(JsonUtils.object_to_json(obj=organization_data,
    #                                                null_sensitive=True))
    #
    #     status, response = self.rest.passthrough.ExecuteRequest(url='/organizations/create-organization',
    #                                                             mode='post',
    #                                                             body=data,
    #                                                             inputParams=None)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Create-organization - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Update organization")
    # def update_organization(self,
    #                         organization_data: OrganizationRestData,
    #                         expected_status_code: int = 200):
    #
    #     json_as_str = JsonUtils.object_to_json(obj=organization_data,
    #                                            null_sensitive=True)
    #     data = json.loads(json_as_str)
    #
    #     status, response = self.rest.passthrough.ExecuteRequest(
    #         url=f'/organizations/update-organization?organization={organization_data.name}',
    #         mode='put',
    #         body=data,
    #         inputParams=None)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Update-organization - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Delete organization")
    # def delete_organization(self,
    #                         organization_name: str,
    #                         expected_status_code: int = 200):
    #
    #     status, response = self.rest.passthrough.ExecuteRequest(
    #         url=f'/organizations/delete-organization?organization={organization_name}',
    #         mode='delete',
    #         body=None,
    #         inputParams=None)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Delete-organization - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Get users")
    # def get_users(self,
    #               organization: str = None,
    #               expected_status_code: int = 200) -> List[dict]:
    #     status, response = self.rest.users.ListUsers(organization=organization)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"List users - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    #     as_list_of_dicts = json.loads(response.content)
    #     return as_list_of_dicts
    #
    # @allure.step("Create user")
    # def create_user(self,
    #                 user_data: CreateUserRestData,
    #                 expected_status_code: int = 200):
    #
    #     status, response = self.rest.users.CreateUser(username=user_data.username,
    #                                                   organization=user_data.organization,
    #                                                   password=user_data.password,
    #                                                   roles=[user_role.value for user_role in user_data.roles],
    #                                                   firstName=user_data.firstName,
    #                                                   lastName=user_data.lastName,
    #                                                   email=user_data.email,
    #                                                   title=user_data.title)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Create-user - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Update user")
    # def update_user(self,
    #                 user_data: UserRestData,
    #                 expected_status_code: int = 200):
    #     status, response = self.rest.users.UpdateUser(username=user_data.username,
    #                                                   organization=user_data.organization,
    #                                                   roles=user_data.roles,
    #                                                   firstName=user_data.firstName,
    #                                                   lastName=user_data.lastName,
    #                                                   email=user_data.email,
    #                                                   title=user_data.title,
    #                                                   new_username=None)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Update-user - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Delete user")
    # def delete_user(self,
    #                 user_name: str,
    #                 organization: str = None,
    #                 expected_status_code: int = 200):
    #     status, response = self.rest.users.DeleteUser(username=user_name,
    #                                                   organization=organization)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Delete user - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Reset user password")
    # def reset_user_password(self, user_name: str, new_password: str, organization: str, expected_status_code: int = 200):
    #     status, response = self.rest.users.ResetPassword(username=user_name,
    #                                                      password=new_password,
    #                                                      organization=organization)
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Reset user password - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    # @allure.step("Get Collector Groups in organization {organization_name}")
    # def get_collector_groups(self,
    #                          organization_name="Default",
    #                          expected_status_code: int = 200):
    #     status, response = self.rest.inventory.ListCollectorGroups(organization=organization_name)
    #
    #     self._validate_expected_status_code(expected_status_code=expected_status_code,
    #                                         actual_status_code=response.status_code,
    #                                         error_message=f"Reset user password - expected response code: {expected_status_code}, actual: {response.status_code}")
    #
    #     as_list_of_dicts = json.loads(response.content)
    #     return as_list_of_dicts