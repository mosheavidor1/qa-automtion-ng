from enum import Enum
import functools
from typing import List

import allure

from infra import common_utils
from infra import enums
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
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.test_im.management_ui_client import ManagementUiClient
from infra.utils.utils import StringUtils


@Singleton
class Management(FortiEdrLinuxStation):
    APPLICATION_PROPERTIES_FILE_PATH = '/opt/FortiEDR/webapp/application.properties'

    _WAIT_MANAGEMENT_SERVICE_TIMEOUT = 120
    _WAIT_MANAGEMENT_SERVICE_INTERVAL = 10
    _DB_TBL_ADM_USERS = 'adm_users'
    _DB_TBL_ADM_USERS_ROLES = 'adm_users_roles'
    _DB_TBL_ADM_ROLES = 'adm_roles'

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
        self.enable_rest_api_for_user_via_db(user_name=self._ui_admin_user_name)

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

        postgresql_server_ip = StringUtils.get_txt_by_regex(text=result,
                                                            regex='spring\.datasource\.url=jdbc:postgresql:\/\/(\w+)',
                                                            group=1)
        if postgresql_server_ip.lower() == 'localhost':
            postgresql_server_ip = '127.0.0.1'

        postgresql_port = StringUtils.get_txt_by_regex(text=result,
                                                       regex='spring\.datasource\.url=jdbc:postgresql:\/\/\w+:(\d+)',
                                                       group=1)
        postgresql_user_name = StringUtils.get_txt_by_regex(text=result,
                                                            regex='spring\.datasource\.username=(\w+)',
                                                            group=1)
        postgresql_password = StringUtils.get_txt_by_regex(text=result,
                                                           regex='spring\.datasource\.password=(\w+)',
                                                           group=1)

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

            elif 'linux' in collector_details.os_family.lower():
                collector = LinuxCollector(host_ip=collector_details.ip_address, user_name=sut_details.linux_user_name,
                                           password=sut_details.linux_password, collector_details=collector_details)
                self._collectors.append(collector)

            # elif 'osx' in collector_details.os_family.lower():
            #     collector = OsXCollector(host_ip=collector_details.ip_address,
            #                              user_name='root',
            #                              password='enSilo$$',
            #                              collector_details=collector_details)
            #
            # else:
            #     raise Exception(
            #         f"Can not create an collector object since collector from the {collector_details.os_family} family is not known by the automation'")

    @allure.step("Check all system components services are up and running")
    def validate_all_system_components_are_running(self):
        # non collector system components inherited from fortiEDRLinuxStation
        non_collector_sys_components = [self] + self._aggregators + self._cores

        with allure.step("Workaround for core - change DeploymentMethod to Cloud although it's onPrem"):
            for core in self.cores:
                content = core.get_file_content(file_path='/opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn')
                deployment_mode = StringUtils.get_txt_by_regex(text=content, regex='"DeploymentMode":"(\w+)"', group=1)
                if deployment_mode == 'OnPremise':
                    core.execute_cmd(
                        """sed -i 's/"DeploymentMode":"OnPremise"/"DeploymentMode":"Cloud"/g' /opt/FortiEDR/core/Config/Core/CoreBootstrap.jsn""")
                    core.stop_service()
                    core.start_service()

        for sys_comp in non_collector_sys_components:
            sys_comp.validate_system_component_is_in_desired_state(desired_state=SystemState.RUNNING)

        for collector in self._collectors:
            assert self.is_collector_status_running_in_mgmt(collector), f"{collector} is not running in {self}"
            Reporter.report(f"Assert that {collector} status is running in CLI")
            assert collector.is_status_running_in_cli(), f"{collector} status is not running"

    @allure.step("Add Rest-API role for {user_name}")
    def enable_rest_api_for_user_via_db(self, user_name='admin'):
        """This functions is adds **Rest API** role to the **'user_name'** provided via SSH > SQL.
        The way it used to set the role via SSH > SQL is to prevent other not stable methods, but, this way is requires
        service restart due to caching mechanism which reads for changes by 2 ways:
            * Service restarted
            * UI Usage
        The chaching mechanisem has its own timer when it checks for changes,
        hard to know its timing, therefore, service restart preferred.

        Used SQL tables
        ----------
        adm_users_roles : list of user_id and role_id
            List of mapped user_id to a specific role_id
        adm_users : list of users details, 
            List of username details, to get the used_id
        adm_roles : list of roles details, used the role name to get the role_id
        
        Parameters
        ----------
        user_name : str, optional
            Which username will add the Rest API role, by default 'admin'        
        """
        user_id = self._get_user_id_by_username_from_db(user_name)
        role_id = self._get_management_role_id_from_db(enums.ManagementUserRoles.ROLE_REST_API.value)
        is_exist = self._user_id_exist_with_role_id_in_db(user_id, role_id)

        if is_exist:
            Reporter.report(f"Rest API enabled for user: {user_name}, Nothing to do")
            return
        else:
            Reporter.report(f"Finished enabling {enums.ManagementUserRoles.ROLE_REST_API.value}")
            self.add_role_id_with_user_id_db(user_id, role_id)

            Reporter.report(f"Restarting after setting role via database to user '{user_name}'")
            self.restart_service()

            self.wait_till_service_up(timeout=self._WAIT_MANAGEMENT_SERVICE_TIMEOUT,
                                      interval=self._WAIT_MANAGEMENT_SERVICE_INTERVAL)

    @allure.step("Wait till the service is up with timeout set to {timeout} sec.")
    def wait_till_service_up(self, timeout: int = 60, interval: int = 5):
        predict_condition_func = functools.partial(self.is_system_in_desired_state, SystemState.RUNNING)

        common_utils.wait_for_predict_condition(
            predict_condition_func=predict_condition_func,
            timeout_sec=timeout,
            interval_sec=interval
        )

    @allure.step("Adding user ID to role ID in the DB")
    def add_role_id_with_user_id_db(self, user_id, role_id):
        query = f"insert into {self._DB_TBL_ADM_USERS_ROLES} (user_id, role_id) values ({user_id}, {role_id})"
        self._postgresql_db.execute_sql_command(sql_cmd=query)

        user_with_role_exist = self._user_id_exist_with_role_id_in_db(user_id, role_id)
        assert user_with_role_exist, "User ID with role ID doesn't exists in the DB and unable to add one :("

    @allure.step("Check if user id({user_id}) is already mapped with role id({expected_role_id})")
    def _user_id_exist_with_role_id_in_db(self, user_id, expected_role_id) -> bool:
        user_roles = self._postgresql_db.execute_sql_command(
            sql_cmd=f"select role_id from {self._DB_TBL_ADM_USERS_ROLES} where user_id={user_id}")
        for user_role in user_roles:
            if user_role.get('role_id') == expected_role_id:
                Reporter.report(f"Role ID is already enabled for user id: {user_id}, expected role ID: {expected_role_id}")
                return True

        return False

    @allure.step("Get {user_name} user_id from db")
    def _get_user_id_by_username_from_db(self, user_name) -> int:
        users_table_results = self._postgresql_db.execute_sql_command(
            sql_cmd=f"select id from {self._DB_TBL_ADM_USERS} where username ='{user_name}'")
        assert len(users_table_results) == 1, f"Issue with finding user_id for the user '{user_name}'.({len(users_table_results)})"

        user_id = users_table_results[0].get('id')
        return user_id

    @allure.step("Get {user_role} id from db")
    def _get_management_role_id_from_db(self, user_role) -> int:
        users_roles_results = self._postgresql_db.execute_sql_command(
            sql_cmd=f"select id from {self._DB_TBL_ADM_ROLES} where authority = '{user_role}'")
        assert len(users_roles_results) == 1, f"Issue with finding role_id for the role.({len(users_roles_results)})"

        role_id = users_roles_results[0].get('id')
        return role_id

    @allure.step("Get collector {collector_ip} state")
    def get_collector_status(self, collector_ip: str) -> SystemState:
        """
        This method return collector state via REST API
        :param collector_ip: collector ip
        :return: SystemState
        """
        all_collectors_info = self.rest_api_client.get_collector_info()
        relevant_collector_info = None
        for collector_info in all_collectors_info:
            if collector_info.get('ipAddress') == collector_ip:
                relevant_collector_info = collector_info
                break

        if relevant_collector_info is None:
            assert False, f"Did not found info about collector with the IP: {collector_ip} in Management"

        Reporter.report(f"Collector state is: {relevant_collector_info.get('state')}")

        if relevant_collector_info.get('state') == 'Running':
            return SystemState.RUNNING

        elif relevant_collector_info.get('state') == 'Disconnected':
            return SystemState.DISCONNECTED

        return SystemState.NOT_RUNNING

    def is_collector_status_running_in_mgmt(self, collector):
        Reporter.report(f"Validate {collector} status is running in {self}")
        collector_ip = collector.os_station.host_ip
        return self.get_collector_status(collector_ip) == SystemState.RUNNING

    def is_collector_status_disconnected_in_mgmt(self, collector):
        collector_ip = collector.os_station.host_ip
        return self.get_collector_status(collector_ip) == SystemState.DISCONNECTED

    def turn_on_prevention_mode(self, organization=None):
        self.rest_api_client.set_policy_mode(self.rest_api_client.rest.NsloPolicies.NSLO_POLICY_EXECUTION_PREVENTION,
                                             self.rest_api_client.rest.NSLO_PREVENTION_MODE, organization)
        self.rest_api_client.set_policy_mode(self.rest_api_client.rest.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION,
                                             self.rest_api_client.rest.NSLO_PREVENTION_MODE, organization)
        self.rest_api_client.set_policy_mode(self.rest_api_client.rest.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION,
                                             self.rest_api_client.rest.NSLO_PREVENTION_MODE, organization)
