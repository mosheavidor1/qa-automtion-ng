import logging
import time

import allure
import functools

from infra.allure_report_handler.reporter import Reporter
from infra import common_utils
from infra.containers.postgresql_over_ssh_details import PostgresqlOverSshDetails
from infra.containers.ssh_details import SshDetails
from infra.forti_edr_versions_service_handler.forti_edr_versions_service_handler import FortiEdrVersionsServiceHandler
from infra.multi_tenancy.tenant import Tenant
from infra.posgresql_db.postgresql_db import PostgresqlOverSshDb
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.api_object_factory.organizations_factory import get_default_organization
from infra.api.management_api.organization import DEFAULT_LICENSE_CAPACITY
import sut_details
from infra.containers.system_component_containers import ManagementDetails
from infra.enums import ComponentType, FortiEdrSystemState, ManagementUserRoles
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation

from infra.test_im.management_ui_client import ManagementUiClient
from infra.utils.utils import StringUtils
from third_party_details import SHARED_DRIVE_COLLECTORS_CONTENT

logger = logging.getLogger(__name__)


class Management(FortiEdrLinuxStation):
    APPLICATION_PROPERTIES_FILE_PATH = '/opt/FortiEDR/webapp/application.properties'

    _WAIT_MANAGEMENT_SERVICE_TIMEOUT = 120
    _WAIT_MANAGEMENT_SERVICE_INTERVAL = 10
    _DB_TBL_ADM_USERS = 'adm_users'
    _DB_TBL_ADM_USERS_ROLES = 'adm_users_roles'
    _DB_TBL_ADM_ROLES = 'adm_roles'

    def __init__(
            self,
            host_ip: str,
            ssh_user_name: str,
            ssh_password: str,
            rest_api_user: str,
            rest_api_user_password: str,
            default_organization_registration_password: str,
            is_licensed: bool = True,
            forced_version: str = None,
    ):
        logger.info(
            f"Trying to init management object with user_name: {ssh_user_name},"
            f" password: {ssh_password}")

        super().__init__(
            host_ip=host_ip,
            user_name=ssh_user_name,
            password=ssh_password,
            component_type=ComponentType.MANAGEMENT)

        self._rest_api_user_name = rest_api_user
        self._rest_api_user_password = rest_api_user_password
        self._registration_password = default_organization_registration_password

        self._postgresql_db: PostgresqlOverSshDb = self._get_postgresql_db_obj()
        self.enable_rest_api_for_user_via_db(user_name=self._rest_api_user_name)

        self._admin_rest_api_client = RestCommands(
            management_ip=host_ip,
            rest_api_user_name=rest_api_user,
            rest_api_user_password=rest_api_user_password,
            organization=None,
            forced_version=forced_version,
        )

        self._temp_tenants = []
        self._details: ManagementDetails | None = None
        self._default_tenant: Tenant | None = None
        self._ui_client: ManagementUiClient | None = None

        if is_licensed:
            self.finish_init_with_license()


    @property
    def rest_api_user_name(self) -> str:
        return self._rest_api_user_name

    @property
    def rest_api_user_password(self) -> str:
        return self._rest_api_user_password

    @property
    def registration_password(self) -> str:
        """ Password for registering collectors to this MGMT """
        return self._registration_password

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

    def finish_init_with_license(self):
        self._details = self._get_management_details()
        reduce_default_org_license_capacity()
        self._default_tenant = self._create_default_tenant()
        self._ui_client = ManagementUiClient(
            management_ui_ip=self.host_ip,
            tenant=self._default_tenant,
        )

    def get_logs_folder_path(self):
        return '/opt/FortiEDR/webapp/logs'

    def _get_management_details(self):
        as_dict = self._admin_rest_api_client.administrator.get_system_summery()
        return ManagementDetails(license_expiration_date=as_dict.get('licenseExpirationDate'),
                                 management_version=as_dict.get('managementVersion'),
                                 management_hostname=as_dict.get('managementHostname'),
                                 management_external_ip=as_dict.get('managementExternalIP'),
                                 management_internal_ip=as_dict.get('managementInternalIP'),
                                 work_stations_collectors_in_use=as_dict.get('workstationsCollectorsInUse'),
                                 work_station_collectors_license_capacity=as_dict.get('workstationCollectorsLicenseCapacity')
                                 )

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
            interval_sec=interval,
            condition_msg="Management service is up"
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
    def wait_until_rest_api_available(self, timeout: int = 60, interval: int = 5):
        start_time = time.time()
        aggregators = None
        while time.time() - start_time < timeout and aggregators is None:
            try:
                aggregators = self._admin_rest_api_client.system_inventory.get_aggregator_info()
            except Exception as e:
                logger.info("Rest API is not available yet, going to sleep 5 sceonds")
                time.sleep(interval)

        assert aggregators is not None, f"REST API is not available within timeout of {timeout}"

    def _create_default_tenant(self) -> Tenant:
        """ This is the main tenant in the test session, can't be deleted """
        logger.info("Create the default tenant")
        collector_type_name = sut_details.collector_type
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
        try:
            temp_tenant.default_local_admin._delete(rest_client=self._admin_rest_api_client,
                                                    expected_status_code=expected_status_code)
        finally:
            temp_tenant.organization._delete(expected_status_code=expected_status_code)
            self.temp_tenants.remove(temp_tenant)

    def get_aggregators(self):
        aggregators = self._admin_rest_api_client.system_inventory.get_aggregator_info()
        return aggregators

    def get_cores(self):
        cores = self._admin_rest_api_client.system_inventory.get_core_info()
        return cores

    @allure.step("Upload content to management")
    def upload_content(self, desired_content_num: int):
        """
        :param desired_content_num: content version to upgrade.
        :return: True if the content uploaded successfully or if the content already exist.
                 False if the content failed uploading or if file doesn't exist.
        """
        content_version = str(desired_content_num)
        result = FortiEdrVersionsServiceHandler.get_latest_content_files_from_shared_folder(num_last_content_files=100)
        content_file_name = f"FortiEDRCollectorContent-{content_version}.nslo"

        if f"FortiEDRCollectorContent-{content_version}.nslo" not in result:
            assert False, f"Can not find content file {content_file_name} in shared folder"

        else:
            path = fr"{SHARED_DRIVE_COLLECTORS_CONTENT}\{content_file_name}"
            Reporter.report(f"Upload content file from: {path}", logger_func=logger.info)

            status = self._admin_rest_api_client.rest.admin.UploadContent(path)

            if not status:
                assert False, "Failed to upload content to management"

        Reporter.report("Content uploaded successfully :)", logger_func=logger.info)

    @allure.step("Upgrade collector with selected version")
    def update_collector_installer(self,
                                   collector_groups: str,
                                   organization: str,
                                   windows_version: str,
                                   osx_version: str,
                                   linux_version: str):
        """
        :param collector_groups: What collector group is going to be upgrade.
                organization: In what organization is the collector group.
                windows_version, osx_version, linux_version: Fill the version according to collector OS.

        :return: True if collector succeeded to upgrade.
                 False if the upgrade collector failed.
        """
        status, response = self._admin_rest_api_client.rest.admin.UpdateCollectorInstaller(
            collector_groups=collector_groups,
            organization=organization, windows_version=windows_version, osx_version=osx_version,
            linux_version=linux_version)

        if response.status_code != 200:
            assert False, f"Update collector installer API - expected response code: {200}, actual:{response.status_code}"

        if not status:
            assert False, f'Could not get response from the management. \n{response}'
        return True

    @allure.step("Upload new license")
    def upload_license_blob(self, license_blob: str):
        uploaded = self._admin_rest_api_client.administrator.upload_license(license_blob=license_blob)
        assert uploaded, "License upload failed"


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
