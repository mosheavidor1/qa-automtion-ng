from typing import List

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.containers.postgresql_over_ssh_details import PostgresqlOverSshDetails
from infra.containers.ssh_details import SshDetails
from infra.posgresql_db.postgresql_db import PostgresqlOverSshDb
from infra.rest.rest_commands import RestCommands

import sut_details
from infra.containers.system_component_containers import AggregatorDetails, CoreDetails, CollectorDetails, \
    ManagementDetails
from infra.enums import ComponentType, OsTypeEnum, SystemState
from infra.singleton import Singleton
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from infra.system_components.core import Core
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation
from infra.system_components.windows_collector import WindowsCollector
from infra.test_im.management_ui_client import ManagementUiClient
from infra.utils.utils import StringUtils


@Singleton
class Management(FortiEdrLinuxStation):

    APPLICATION_PROPERTIES_FILE_PATH = '/opt/FortiEDR/webapp/application.properties'

    def __init__(self):

        super().__init__(
            host_ip=sut_details.management_host,
            user_name=sut_details.management_ssh_user_name,
            password=sut_details.management_ssh_password,
            component_type=ComponentType.MANAGEMENT)

        self._ui_admin_user_name = sut_details.management_ui_admin_user_name
        self._ui_admin_password = sut_details.management_ui_admin_password
        self._registration_password = sut_details.management_registration_password
        self._aggregators: [Aggregator] = []
        self._cores: [Core] = []
        self._collectors: [Collector] = []

        self._postgresql_db: PostgresqlOverSshDb = self._get_postgresql_db_obj()
        self.enable_rest_api_for_user_via_db(user_name='admin')

        self._rest_api_client = RestCommands(self.host_ip,
                                             self._ui_admin_user_name,
                                             self._ui_admin_password,
                                             organization=None)

        self._ui_client = ManagementUiClient(management_ui_ip=self.host_ip)

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

    @property
    def registration_password(self) -> str:
        """ Password for registering collectors to this MGMT """
        return self._registration_password

    @ui_admin_password.setter
    def ui_admin_password(self, ui_admin_password: str):
        self._ui_admin_password = ui_admin_password

    @property
    def aggregators(self) -> List[Aggregator]:
        return self._aggregators

    @aggregators.setter
    def aggregators(self, aggregators: List[Aggregator]):
        self._aggregators = aggregators

    @property
    def cores(self) -> List[Core]:
        return self._cores

    @cores.setter
    def cores(self, cores: List[Core]):
        self._cores = cores

    @property
    def collectors(self) -> List[Collector]:
        return self._collectors

    @collectors.setter
    def collectors(self, collectors: List[Collector]):
        self._collectors = collectors

    @property
    def rest_api_client(self) -> RestCommands:
        return self._rest_api_client

    @property
    def ui_client(self) -> ManagementUiClient:
        return self._ui_client

    @property
    def details(self) -> ManagementDetails:
        return self._details

    @property
    def postgresql_db(self) -> PostgresqlOverSshDb:
        return self._postgresql_db

    def __repr__(self):
        return f"Management {self._host_ip}"

    def get_logs_folder_path(self):
        return '/opt/FortiEDR/webapp/logs'

    def _get_management_details(self):
        as_dict = self._rest_api_client.get_system_summery()
        return ManagementDetails(license_expiration_date=as_dict.get('licenseExpirationDate'),
                                 management_version=as_dict.get('managementVersion'),
                                 management_hostname=as_dict.get('managementHostname'),
                                 management_external_ip=as_dict.get('managementExternalIP'),
                                 management_internal_ip=as_dict.get('managementInternalIP'))

    def _get_postgresql_db_obj(self) -> PostgresqlOverSshDb:
        ssh_details = SshDetails(host_ip=self.host_ip, user_name=self.user_name, password=self.password)

        cmd = f'{self.APPLICATION_PROPERTIES_FILE_PATH} | grep spring.datasource'
        result = self.get_file_content(file_path=cmd)

        postgresql_server_ip = StringUtils.get_txt_by_regex(text=result, regex='spring\.datasource\.url=jdbc:postgresql:\/\/(\w+)', group=1)
        if postgresql_server_ip.lower() == 'localhost':
            postgresql_server_ip = '127.0.0.1'

        postgresql_port = StringUtils.get_txt_by_regex(text=result, regex='spring\.datasource\.url=jdbc:postgresql:\/\/\w+:(\d+)', group=1)
        postgresql_user_name = StringUtils.get_txt_by_regex(text=result, regex='spring\.datasource\.username=(\w+)', group=1)
        postgresql_password = StringUtils.get_txt_by_regex(text=result, regex='spring\.datasource\.password=(\w+)', group=1)

        postgresql_details = PostgresqlOverSshDetails(db_name='ensilo',
                                                      user_name=postgresql_user_name,
                                                      password=postgresql_password,
                                                      server_ip=postgresql_server_ip,
                                                      server_port=int(postgresql_port))
        postgres_db = PostgresqlOverSshDb(ssh_details=ssh_details,
                                          postgresql_details=postgresql_details)
        return postgres_db

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
        aggregators = self._rest_api_client.get_aggregator_info()
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
        cores = self._rest_api_client.get_core_info()
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
        collectors = self._rest_api_client.get_collector_info()

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
        # non collector system components inherited from fortiEDRLinuxStation
        non_collector_sys_components = [self] + self._aggregators + self._cores

        # classic example of polymorphism
        for sys_comp in non_collector_sys_components:
            sys_comp.validate_system_component_is_in_desired_state(desired_state=SystemState.RUNNING)

        for single_collector in self._collectors:
            single_collector.validate_collector_is_up_and_running(use_health_monitor=True)

    @allure.step("Add Rest-API role for {user_name}")
    def enable_rest_api_for_user_via_db(self, user_name='admin'):

        users_table_results = self._postgresql_db.execute_sql_command(sql_cmd=f"select id from adm_users where username = '{user_name}'")
        user_id = users_table_results[0].get('id')

        users_roles_results = self._postgresql_db.execute_sql_command(sql_cmd="select id from adm_roles where authority = 'ROLE_REST_API'")
        role_rest_api_id = users_roles_results[0].get('id')

        specific_user_roles = self._postgresql_db.execute_sql_command(sql_cmd=f"select role_id from adm_users_roles where user_id={user_id}")

        for single_role in specific_user_roles:
            if single_role.get('role_id') == role_rest_api_id:
                Reporter.report(f"Rest API enabled for user: {user_name}, Nothing to do")
                return

        # if we the api role is not set to the specific user we will add it to DB
        query = f"insert into adm_users_roles (user_id, role_id) values ({user_id}, {role_rest_api_id})"
        self._postgresql_db.execute_sql_command(sql_cmd=query)

