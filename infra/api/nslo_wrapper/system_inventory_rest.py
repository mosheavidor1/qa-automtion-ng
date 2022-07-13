import json
from typing import List
import logging
import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.enums import FortiEdrSystemState
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

    @allure.step("Create new group")
    def create_group(self, name):
        logger.info(f"Create new collector group with name {name}")
        status, response = self._rest.inventory.CreateCollectorGroup(group=name)
        assert status, f"Failed to create collector group {name}, got {response}"

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
    def move_collectors_to_organization(self, collectors_names: List[str], target_group_name,
                                        current_collectors_organization, target_organization,
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

    @allure.step("Move collector {collector_name} to group: {group_name} in same organization")
    def move_collector_to_group(self, collector_name, group_name, expected_status_code: int = 200):
        status, response = self._rest.inventory.MoveCollectors(collectors=collector_name, group=group_name)
        assert status, f'Could not get response from the management. \n{response}'
        err_msg = f"Failed to move collector {collector_name} to group {group_name}, " \
                  f"expected response code: {expected_status_code}, actual: {response.status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code, error_message=err_msg)

    @allure.step("{toggle_status} collector via MGMT api")
    def toggle_collector(self, collector_name: str, organization_name: str, toggle_status: FortiEdrSystemState,
                         expected_status_code: int = 200):
        """ Change collector status (disable/enable) via rest api to MGMT """
        logger.info(f"{toggle_status} collector via MGMT api")
        enable = True if toggle_status == FortiEdrSystemState.ENABLED else False
        status, response = self._rest.inventory.ToggleCollectors(
            collectors=[collector_name],
            organization=organization_name,
            enable=enable
        )
        self._validate_expected_status_code(
            expected_status_code=expected_status_code,
            actual_status_code=response.status_code,
            error_message=f"Failed to disable collector, got {response.status_code} instead {expected_status_code}")

    def get_collector_groups(self, organization_name, expected_status_code: int = 200):
        logger.debug(f"Get all collector groups in organization {organization_name}")
        status, response = self._rest.inventory.ListCollectorGroups(organization=organization_name)
        assert status, f"Failed to get collector groups, got: {response}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Get collector groups - expected response code: {expected_status_code}, actual: {response.status_code}")
        collector_groups = json.loads(response.text)
        logger.debug(f"Collector groups are: {collector_groups}")
        return collector_groups

    @allure.step("Delete collectors")
    def delete_collectors(self,
                          collector_names: List[str],
                          expected_status_code: int = 200):

        status, response = self._rest.inventory.DeleteCollectors(devices=collector_names)
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Reset user password - expected response code: {expected_status_code}, actual: {response.status_code}")
