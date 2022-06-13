import json
from typing import List
import logging
import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.enums import SystemState
from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality
from infra.system_components.collector import CollectorAgent
logger = logging.getLogger(__name__)


class SystemInventoryRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    def get_collector_info_by_id(self, collector_id: int, validation_data=None, output_parameters=None):
        status, response = self._rest.inventory.ListCollectors(devicesIds=[collector_id])
        return self._get_info(status, response, 'collector', validation_data, output_parameters)

    def get_collector_info(self, validation_data=None, output_parameters=None, organization=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given collector.
                                  options for collector parameters: 'id', 'name', 'collectorGroupName', 'operatingSystem',
                                                             'ipAddress' (0.0.0.0), 'osFamily', 'state', 'lastSeenTime',
                                                              'version', 'macAddresses', 'loggedUsers'
        :param validation_data: dictionary, the data to get from the collector.
        :return: according to the get_info function.
        """
        status, response = self._rest.inventory.ListCollectors(organization=organization)
        return self._get_info(status, response, 'collector', validation_data, output_parameters)

    def create_group(self, name, organization=None):
        """
        :param name: string, the name of the group.
        :return: True if succeeded creating the group, False if failed.
        """
        group_status, group_response = self._rest.inventory.ListCollectorGroups(organization=organization)
        groups_list = self._get_info(group_status, group_response)

        for group in groups_list:
            if name == group["name"]:
                Reporter.report('group ' + name + ' already exist')
                return True

        status, response = self._rest.inventory.CreateCollectorGroup(group=name)

        group_status, group_response = self._rest.inventory.ListCollectorGroups(organization=organization)
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

    def get_aggregator_info(self, validation_data=None, output_parameters=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given core.
                                  options for collector parameters: 'id', 'hostName', 'ipAddress', 'version',
                                  'numOfAgents', 'numOfDownAgents', 'state'.
        :param validation_data: dictionary, the data to get from the core.
        :return: according to the get_info function.
        """
        status, response = self._rest.inventory.ListAggregators()
        self._validate_expected_status_code(expected_status_code=200,
                                            actual_status_code=response.status_code,
                                            error_message=f"Failed to get aggregator info - expected response code: {200}, actual: {response.status_code}")
        return self._get_info(status, response, 'aggregator', validation_data, output_parameters)

    def get_core_info(self, validation_data=None, output_parameters=None):
        """
        :param output_parameters: string or list, the information parameter to get from the given core.
                                  options for collector parameters: ['deploymentMode', 'ip' ('0.0.0.0:555'), 'name',
                                  'version', 'status']
        :param validation_data: dictionary, the data to get from the core.
        :return: according to the get_info function.
        """
        status, response = self._rest.inventory.ListCores()
        self._validate_expected_status_code(expected_status_code=200,
                                            actual_status_code=response.status_code,
                                            error_message=f"Failed to get core info - expected response code: {200}, actual: {response.status_code}")
        return self._get_info(status, response, 'core', validation_data, output_parameters)

    @allure.step(
        "Move collectors {collectors_names} to group: {target_group_name} in organization: {target_organization}")
    def move_collectors(self,
                        collectors_names: List[str],
                        target_group_name: str = "Default Collector Group",
                        current_collectors_organization: str = "Default",
                        target_organization: str = "Default",
                        expected_status_code: int = 200):

        collectors_to_move = [fr'{current_collectors_organization}\{collector_name}' for collector_name in
                              collectors_names]
        target_collector_group = fr'{target_organization}\{target_group_name}'
        organization = None
        if target_organization != "Default":
            organization = 'All organizations'

        params = {
            'collectors': collectors_to_move,
            'targetCollectorGroup': target_collector_group,
            'organization': organization
        }
        status, response = self._rest.passthrough.ExecuteRequest(url='/inventory/move-collectors',
                                                                 mode='put',
                                                                 inputParams=params)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Move Collector - expected response code: {expected_status_code}, actual: {response.status_code}")

    def move_collector(self,
                       validation_data,
                       group_name: str):
        """
        :param validation_data: dictionary, the data of the collector to be moved.
        :param group_name: string, the name of the group to move the collector to.
        :return: True if succeeded, False if failed.
        """
        collector_name = list(map(lambda x: list(x.values())[0], self.get_collector_info(validation_data, 'name')))
        status, response = self._rest.inventory.MoveCollectors(collectors=collector_name, group=group_name)
        collector_group = self.get_collector_info(validation_data, 'collectorGroupName')
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if collector_group[0]["collectorGroupName"] != group_name:
            assert False, 'Could not move the collector ' + str(
                collector_name) + ' to the group ' + group_name + '.'

        Reporter.report(
            'Moved the collector ' + str(collector_name) + ' to the group ' + group_name + ' successfully.')
        return True

    @allure.step("{toggle_status} collector via MGMT api")
    def toggle_collector(self, collector_name: str, organization_name: str, toggle_status: SystemState,
                         expected_status_code: int = 200):
        """ Change collector status (disable/enable) via rest api to MGMT """
        logger.info(f"{toggle_status} collector via MGMT api")
        enable = True if toggle_status == SystemState.ENABLED else False
        status, response = self._rest.inventory.ToggleCollectors(
            collectors=[collector_name],
            organization=organization_name,
            enable=enable
        )
        self._validate_expected_status_code(
            expected_status_code=expected_status_code,
            actual_status_code=response.status_code,
            error_message=f"Failed to disable collector, got {response.status_code} instead {expected_status_code}")

    @allure.step("Get Collector Groups in organization {organization_name}")
    def get_collector_groups(self,
                             organization_name="Default",
                             expected_status_code: int = 200):
        status, response = self._rest.inventory.ListCollectorGroups(organization=organization_name)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Reset user password - expected response code: {expected_status_code}, actual: {response.status_code}")

        as_list_of_dicts = json.loads(response.content)
        return as_list_of_dicts
