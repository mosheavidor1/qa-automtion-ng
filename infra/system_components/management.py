import allure

from infra.allure_report_handler.reporter import Reporter
from infra.containers.postgresql_over_ssh_details import PostgresqlOverSshDetails
from infra.containers.ssh_details import SshDetails
from infra.posgresql_db.postgresql_db import PostgresqlOverSshDb
from infra.rest.rest_commands import RestCommands

import sut_details
from infra.containers.system_component_containers import ManagementDetails
from infra.enums import ComponentType, SystemState
from infra.singleton import Singleton
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation

from infra.test_im.management_ui_client import ManagementUiClient
from infra.utils.utils import StringUtils
from infra.system_components.collectors.collectors_common_utils import wait_for_running_collector_status_in_mgmt


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

        self._postgresql_db: PostgresqlOverSshDb = self._get_postgresql_db_obj()
        self.enable_rest_api_for_user_via_db(user_name='admin')

        self._rest_api_client = RestCommands(self.host_ip,
                                             self._ui_admin_user_name,
                                             self._ui_admin_password,
                                             organization=None)

        self._ui_client = ManagementUiClient(management_ui_ip=self.host_ip)

        self._details: ManagementDetails = self._get_management_details()

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
