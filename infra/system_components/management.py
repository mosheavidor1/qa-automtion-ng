import json
from typing import List

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest, NsloManagementConnection

import sut_details
from infra.allure_report_handler.reporter import Reporter
from infra.containers.system_component_containers import AggregatorDetails, CoreDetails, CollectorDetails, \
    ManagementDetails
from infra.enums import ComponentType, OsTypeEnum, SystemState, CollectorTypes
from infra.singleton import Singleton
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from infra.system_components.core import Core
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation
from infra.system_components.linux_collector import LinuxCollector
from infra.system_components.os_x_collector import OsXCollector
from infra.system_components.windows_collector import WindowsCollector
from infra.test_im.test_im_handler import TestImHandler
from infra.utils.utils import StringUtils


@Singleton
class Management(FortiEdrLinuxStation):

    def __init__(self):

        super().__init__(
            host_ip=sut_details.management_host,
            user_name=sut_details.management_ssh_user_name,
            password=sut_details.management_ssh_password,
            component_type=ComponentType.MANAGEMENT)

        self._ui_admin_user_name = sut_details.management_ui_admin_user_name
        self._ui_admin_password = sut_details.management_ui_admin_password
        self._aggregators: [Aggregator] = []
        self._cores: [Core] = []
        self._collectors: [Collector] = []

        self._test_im_client: TestImHandler = TestImHandler()
        self._rest_ui_client = NsloRest(NsloManagementConnection(self.host_ip,
                                                                 self._ui_admin_user_name,
                                                                 self._ui_admin_password,
                                                                 organization=None))

        self._details: ManagementDetails = self._get_management_details()
        self.init_system_objects()

    @property
    def ui_admin_user_name(self) -> str:
        return self._ui_admin_user_name

    @ui_admin_user_name.setter
    def ui_admin_user_name(self, ui_admin_user_name: str):
        self._ui_admin_user_name = ui_admin_user_name

    @property
    def ui_admin_password(self) -> str:
        return self._ui_admin_password

    @ui_admin_password.setter
    def ui_admin_password(self, ui_admin_password: str):
        self._ui_admin_password = ui_admin_password

    @property
    def aggregators(self) -> [Aggregator]:
        return self._aggregators

    @aggregators.setter
    def aggregators(self, aggregators: [Aggregator]):
        self._aggregators = aggregators

    @property
    def cores(self) -> [Core]:
        return self._cores

    @cores.setter
    def cores(self, cores: [Core]):
        self._cores = cores

    @property
    def collectors(self) -> List[Collector]:
        return self._collectors

    @collectors.setter
    def collectors(self, collectors: [Collector]):
        self._collectors = collectors

    @property
    def rest_ui_client(self) -> NsloRest:
        return self._rest_ui_client

    @property
    def details(self) -> ManagementDetails:
        return self._details

    @property
    def test_im_client(self) -> TestImHandler:
        return self._test_im_client

    def __repr__(self):
        return f"Management {self._host_ip}"

    def get_logs_folder_path(self):
        return '/opt/FortiEDR/webapp/logs'

    def _get_management_details(self):
        response = self._rest_ui_client.admin.GetSystemSummary()
        response = response[1]
        as_dict = json.loads(response.content)
        return ManagementDetails(license_expiration_date=as_dict.get('licenseExpirationDate'),
                                 management_version=as_dict.get('managementVersion'),
                                 management_hostname=as_dict.get('managementHostname'),
                                 management_external_ip=as_dict.get('managementExternalIP'),
                                 management_internal_ip=as_dict.get('managementInternalIP'))

    @allure.step("Init system objects")
    def init_system_objects(self):
        """
        The role of this method is to init system objects which connected to this manager
        """
        self.init_aggregator_objects()
        self.init_core_objects()
        self.init_collector_objects()

    @allure.step("Init aggregator objects")
    def init_aggregator_objects(self):
        response = self._rest_ui_client.inventory.ListAggregators()
        response = response[1]
        aggregators = json.loads(response.content)
        for single_aggr in aggregators:

            ip_addr, port = StringUtils.get_ip_port_as_tuple(single_aggr.get('ipAddress'))

            aggregator_details = AggregatorDetails(host_name=single_aggr.get('hostName'),
                                                   system_id=single_aggr.get('id'),
                                                   version=single_aggr.get('version'),
                                                   ip_address=ip_addr,
                                                   port=port,
                                                   num_of_agents=single_aggr.get('numOfAgents'),
                                                   num_of_down_agents=single_aggr.get('numOfDownAgents'),
                                                   state=single_aggr.get('state'),
                                                   organization=single_aggr.get('organization'))

            host_ip = self._host_ip if '127.0.0.1' in aggregator_details.ip_address else aggregator_details.ip_address

            new_aggr = Aggregator(host_ip=host_ip,
                                  aggregator_details=aggregator_details)
            self._aggregators.append(new_aggr)

    @allure.step("Init core objects")
    def init_core_objects(self):
        response = self._rest_ui_client.inventory.ListCores()
        response = response[1]
        cores = json.loads(response.content)
        for single_core in cores:
            ip_addr, port = StringUtils.get_ip_port_as_tuple(single_core.get('ip'))

            core_details = CoreDetails(system_id=single_core.get('id'),
                                       deployment_mode=single_core.get('deploymentMode'),
                                       ip=ip_addr,
                                       port=port,
                                       name=single_core.get('name'),
                                       version=single_core.get('version'),
                                       status=single_core.get('status'),
                                       organization=single_core.get('organization'),
                                       functionality=single_core.get('functionality'))
            core = Core(host_ip=core_details.ip, core_details=core_details)
            self._cores.append(core)

    @allure.step("Init collector objects")
    def init_collector_objects(self):
        response = self._rest_ui_client.inventory.ListCollectors()
        response = response[1]
        collectors = json.loads(response.text)

        for single_collector in collectors:
            collector_details = CollectorDetails(system_id=single_collector.get('id'),
                                                 name=single_collector.get('name'),
                                                 collector_group_name=single_collector.get('collectorGroupName'),
                                                 operating_system=single_collector.get('operatingSystem'),
                                                 ip_address=single_collector.get('ipAddress'),
                                                 last_seen_time=single_collector.get('lastSeenTime'),
                                                 mac_addresses=single_collector.get('macAddresses'),
                                                 account_name=single_collector.get('accountName'),
                                                 organization=single_collector.get('organization'),
                                                 state=single_collector.get('state'),
                                                 os_family=single_collector.get('osFamily'),
                                                 state_additional_info=single_collector.get('stateAdditionalInfo'),
                                                 version=single_collector.get('version'),
                                                 logged_users=single_collector.get('loggedUsers'),
                                                 system_information=single_collector.get('systemInformation'))
            os_type = OsTypeEnum.LINUX
            collector = None
            if 'win' in collector_details.os_family.lower():

                user_name = sut_details.win_user_name
                password = sut_details.win_password

                encrypted_connection = True
                if "windows 7" in collector_details.operating_system.lower():
                    encrypted_connection = False

                # collector = WindowsCollector(host_ip=collector_details.ip_address,
                #                              user_name=sut_details.win_user_name,
                #                              password=sut_details.win_password,
                #                              collector_details=collector_details,
                #                              encrypted_connection=encrypted_connection)

                # all this part below is a workaround because there is different users & passwords for various operating systems
                # should be removed when we will have templated with the same user name and password for all windows versions.
                elif "windows server 2019" in collector_details.operating_system.lower():
                    user_name = 'Administrator'
                    password = 'enSilo$$'

                elif "windows 8.1" in collector_details.operating_system.lower():
                    user_name = 'root'
                    password = 'root'

                collector = WindowsCollector(host_ip=collector_details.ip_address,
                                             user_name=user_name,
                                             password=password,
                                             collector_details=collector_details,
                                             encrypted_connection=encrypted_connection)

                collector.os_station.user_name = user_name
                collector.os_station.password = password

                self._collectors.append(collector)


            # TBD - Uncomment when the logic of linux collector will be implemented

            # elif 'ubunto' in collector_details.os_family.lower() \
            #         or 'centos' in collector_details.os_family.lower() \
            #         or 'oracle' in collector_details.os_family.lower() \
            #         or 'suse' in collector_details.os_family.lower() \
            #         or 'amazon' in collector_details.os_family.lower():
            #
            #     collector = LinuxCollector(host_ip=collector_details.ip_address,
            #                                user_name='root',
            #                                password='enSilo$$',
            #                                collector_details=collector_details)
            #
            # elif 'osx' in collector_details.os_family.lower():
            #     collector = OsXCollector(host_ip=collector_details.ip_address,
            #                              user_name='root',
            #                              password='enSilo$$',
            #                              collector_details=collector_details)
            #
            # else:
            #     raise Exception(
            #         f"Can not create an collector object since collector from the {collector_details.os_family} family is not known by the automation'")
            #
            # self._collectors.append(collector)

    @allure.step("Check all system components services are up and running")
    def validate_all_system_components_are_running(self):
        non_collector_sys_components = [self] + self._aggregators + self._cores

        for sys_comp in non_collector_sys_components:
            sys_comp.validate_system_component_is_in_desired_state(desired_state=SystemState.RUNNING)

        for single_collector in self._collectors:
            single_collector.validate_collector_is_up_and_running(use_health_monitor=True)

    @allure.step("Clear logs from all system components")
    def clear_logs_from_all_system_components(self):
        all_sys_comp = [self] + self._aggregators + self._cores + self._collectors
        for sys_comp in all_sys_comp:
            file_suffix = '.log'

            if isinstance(sys_comp, Collector) or isinstance(sys_comp, Core):

                if isinstance(sys_comp, Collector):
                    # TBD - not implement yet, this if should be removed after the implementation
                    continue

                file_suffix = '.blg'

            sys_comp.clear_logs(file_suffix=file_suffix)

    @allure.step("Append logs to report")
    def append_logs_to_report_from_all_system_components(self):
        all_sys_comp = [self] + self._aggregators + self._cores + self._collectors
        for sys_comp in all_sys_comp:

            if isinstance(sys_comp, Collector):
                # TBD
                continue

            if isinstance(sys_comp, Core):
                logs_folder_path = sys_comp.get_logs_folder_path()
                blg_log_files = sys_comp.get_list_of_files_in_folder(logs_folder_path)
                blg_log_files = [f'{logs_folder_path}/{single_file}' for single_file in blg_log_files]
                sys_comp.parse_blg_log_files(blg_log_files_paths=blg_log_files)

            sys_comp.append_logs_to_report(file_suffix='.log')




