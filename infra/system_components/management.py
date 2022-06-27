import logging
import time

import allure
import functools

from infra.allure_report_handler.reporter import Reporter
from infra import common_utils
from infra.containers.postgresql_over_ssh_details import PostgresqlOverSshDetails
from infra.containers.ssh_details import SshDetails
from infra.multi_tenancy.tenant import Tenant
from infra.posgresql_db.postgresql_db import PostgresqlOverSshDb
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.api_object_factory.organizations_factory import get_default_organization
from infra.api.management_api.organization import DEFAULT_LICENSE_CAPACITY
import sut_details
from infra.containers.system_component_containers import ManagementDetails
from infra.enums import ComponentType, FortiEdrSystemState, ManagementUserRoles
from infra.singleton import Singleton
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation

from infra.test_im.management_ui_client import ManagementUiClient
from infra.utils.utils import StringUtils
logger = logging.getLogger(__name__)


@Singleton
class Management(FortiEdrLinuxStation):
    APPLICATION_PROPERTIES_FILE_PATH = '/opt/FortiEDR/webapp/application.properties'

    _WAIT_MANAGEMENT_SERVICE_TIMEOUT = 120
    _WAIT_MANAGEMENT_SERVICE_INTERVAL = 10
    _DB_TBL_ADM_USERS = 'adm_users'
    _DB_TBL_ADM_USERS_ROLES = 'adm_users_roles'
    _DB_TBL_ADM_ROLES = 'adm_roles'

    def __init__(self):
        self._config = sut_details
        logger.info(
            f"Trying to init management object with user_name: {self._config.management_ssh_user_name},"
            f" password: {self._config.management_ssh_password}")

        super().__init__(
            host_ip=self._config.management_host,
            user_name=self._config.management_ssh_user_name,
            password=self._config.management_ssh_password,
            component_type=ComponentType.MANAGEMENT)

        self._ui_admin_user_name = self._config.management_ui_admin_user_name
        self._ui_admin_password = self._config.management_ui_admin_password
        self._registration_password = self._config.management_registration_password

        self._postgresql_db: PostgresqlOverSshDb = self._get_postgresql_db_obj()
        self.enable_rest_api_for_user_via_db(user_name=self._ui_admin_user_name)

        self._admin_rest_api_client = RestCommands(self.host_ip,
                                                   self._ui_admin_user_name,
                                                   self._ui_admin_password,
                                                   organization=None)

        self._details: ManagementDetails = self._get_management_details()
        reduce_default_org_license_capacity()
        self._temp_tenants = []
        self._default_tenant: Tenant = self._create_default_tenant()
        self._ui_client = ManagementUiClient(management_ui_ip=self.host_ip,
                                             tenant=self._default_tenant)

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
    def admin_rest_api_client(self) -> RestCommands:
        return self._admin_rest_api_client

    @property
    def ui_client(self) -> ManagementUiClient:
        return self._ui_client

    @property
    def details(self) -> ManagementDetails:
        return self._details

    @property
    def postgresql_db(self) -> PostgresqlOverSshDb:
        return self._postgresql_db

    @property
    def tenant(self) -> Tenant:
        """ Return the default tenant: The main tenant that is under test, can't be deleted """
        return self._default_tenant

    @property
    def temp_tenants(self):
        """ Return the temporary tenants, that created during test and should be deleted at the end """
        return self._temp_tenants

    def __repr__(self):
        return f"Management {self._host_ip}"

    def get_logs_folder_path(self):
        return '/opt/FortiEDR/webapp/logs'

    def _get_management_details(self):
        as_dict = self._admin_rest_api_client.administrator.get_system_summery()
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
        role_id = self._get_management_role_id_from_db(ManagementUserRoles.ROLE_REST_API.value)
        is_exist = self._user_id_exist_with_role_id_in_db(user_id, role_id)

        if is_exist:
            Reporter.report(f"Rest API enabled for user: {user_name}, Nothing to do")
            return
        else:
            Reporter.report(f"Finished enabling {ManagementUserRoles.ROLE_REST_API.value}")
            self.add_role_id_with_user_id_db(user_id, role_id)

            Reporter.report(f"Restarting after setting role via database to user '{user_name}'")
            self.restart_service()

            self.wait_till_service_up(timeout=self._WAIT_MANAGEMENT_SERVICE_TIMEOUT,
                                      interval=self._WAIT_MANAGEMENT_SERVICE_INTERVAL)

    @allure.step("Wait till the service is up with timeout set to {timeout} sec.")
    def wait_till_service_up(self, timeout: int = 60, interval: int = 5):
        predict_condition_func = functools.partial(self.is_system_in_desired_state, FortiEdrSystemState.RUNNING)

        common_utils.wait_for_condition(
            condition_func=predict_condition_func,
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

    @allure.step("Wait until rest api available")
    def wait_until_rest_api_available(self, timeout: int = 60):
        start_time = time.time()
        aggregators = None
        while time.time() - start_time < timeout and aggregators is None:
            try:
                aggregators = self.admin_rest_api_client.system_inventory.get_aggregator_info()
            except Exception as e:
                logger.info("Rest API is not available yet, going to sleep 5 sceonds")
                time.sleep(5)

        assert aggregators is not None, f"REST API is not available within timeout of {timeout}"

    def _create_default_tenant(self) -> Tenant:
        """ This is the main tenant in the test session, can't be deleted """
        logger.info("Create the default tenant")
        collector_type_name = self._config.collector_type
        default_tenant = Tenant.create(username=collector_type_name, user_password=collector_type_name,
                                       organization_name=collector_type_name, registration_password=collector_type_name)
        return default_tenant

    def create_temp_tenant(self, user_name, user_password, organization_name, registration_password) -> Tenant:
        """ Create tenant for testing that should be deleted afterwards """
        logger.info(f"Create temp tenant with user {user_name} and organization {organization_name}")
        for tenant in self._temp_tenants:
            assert organization_name != tenant.organization.get_name(), \
                f"Temp tenant with org name {organization_name} already created"
        tenant = Tenant.create(username=user_name, user_password=user_password, organization_name=organization_name,
                               registration_password=registration_password)
        self._temp_tenants.append(tenant)
        return tenant

    @allure.step("Delete temp tenant")
    def delete_tenant(self, temp_tenant: Tenant, expected_status_code=200):
        """ Use management admin credentials to delete the default user and the organization of a temp tenant"""
        logger.info(f"Delete temp tenant: {temp_tenant}")
        assert temp_tenant.organization.id != self.tenant.organization.id, \
            f"{temp_tenant} is the default tenant of management so can't be deleted"
        temp_tenant.default_local_admin._delete(rest_client=self.admin_rest_api_client,
                                                expected_status_code=expected_status_code)
        temp_tenant.organization._delete(expected_status_code=expected_status_code)
        self.temp_tenants.remove(temp_tenant)


def reduce_default_org_license_capacity():
    """ The default organization occupies all the available licence capacity (~10,000).
        Therefore, we don't have free licence capacity to create collectors in other organizations.
        So, in order to create collectors in other organizations, first we need to free some licence capacity.
        Therefore, we must reduce the default organization's licence capacity to smaller capacity """
    default_organization = get_default_organization()
    default_organization_license_capacity = default_organization.get_servers_licences_capacity(from_cache=True)
    if default_organization_license_capacity > DEFAULT_LICENSE_CAPACITY:
        logger.info("Reduce the licence capacity of the default organization")
        default_organization.update_license_capacity(new_license_capacity=DEFAULT_LICENSE_CAPACITY)
