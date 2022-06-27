import datetime
import json
import random
import time
from typing import List

import allure

import sut_details
import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.containers.environment_creation_containers import EnvironmentSystemComponent, DeployedEnvInfo
from infra.enums import HttpRequestMethodsEnum, AutomationVmTemplates, ComponentType, \
    CleanVMsReadyForCollectorInstallation
from infra.os_stations.linux_station import LinuxStation
from infra.system_components.aggregator import Aggregator
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.core import Core
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation
from infra.utils.utils import JsonUtils, HttpRequesterUtils, StringUtils
from infra.vpshere.vsphere_cluster_handler import VsphereClusterHandler, VmSearchTypeEnum
from infra.vpshere.vsphere_vm_operations import VsphereMachineOperations


def _is_vm_free_to_use(vm_ops: VsphereMachineOperations,
                       collector_vm: CleanVMsReadyForCollectorInstallation):
    """
    we are using this method in order to understand of VM is free and can be allocated to specific management
    :return: boolean
    """
    if vm_ops.is_power_off() and vm_ops.vm_obj.name == collector_vm.value:
        return True

    return False

def _get_core_config_cmd(desired_hostname: str,
                         date_time: str,
                         date_date: str,
                         core_external_ip_address: str,
                         registration_password: str,
                         aggregator_ip: str,
                         timezone: str = 'Asia/Jerusalem'):
    cmd = f"fortiedr config --silent " \
          f"--Hostname '{desired_hostname}' " \
          f"--Role core " \
          f"--TimeZone '{timezone}' " \
          f"--Time {date_time} " \
          f"--Date {date_date} " \
          f"--CoreExternalIpAddress {core_external_ip_address} " \
          f"--RegistrationPassword {registration_password} " \
          f"--AggregatorAddress {aggregator_ip}"

    return cmd


def _get_aggregator_config_cmd(desired_hostname: str,
                               date_time: str,
                               date_date: str,
                               management_host_ip: str,
                               management_registration_password: str,
                               timezone: str = 'Asia/Jerusalem'):
    cmd = f"fortiedr config " \
          f"--silent " \
          f"--Hostname '{desired_hostname}' " \
          f"--Role aggregator " \
          f"--TimeZone '{timezone}' " \
          f"--Time {date_time} " \
          f"--Date {date_date} " \
          f"--ManagementIpAddress {management_host_ip} " \
          f"--RegistrationPassword {management_registration_password}"

    return cmd


def _get_management_config_cmd(desired_hostname: str,
                               date_time: str,
                               date_date: str,
                               timezone='Asia/Jerusalem',
                               both=False):
    management_type = 'manager'

    if both:
        management_type = 'both'

    cmd = f"fortiedr config " \
          f"--silent " \
          f"--Hostname '{desired_hostname}' " \
          f"--Role {management_type} " \
          f"--TimeZone '{timezone}' " \
          f"--Time {date_time} " \
          f"--Date {date_date} "

    return cmd


class EnvironmentCreationHandler:

    BUSY_VM_COLLECTOR = 'busy_'

    @staticmethod
    @allure.step("Deploy system components using deployment service")
    def deploy_system_components_external_service(environment_name: str,
                                                  system_components: List[EnvironmentSystemComponent],
                                                  installation_type: str = 'qa') -> str:
        url = f'{third_party_details.ENVIRONMENT_SERVICE_URL}/api/v1/fedr/environment'

        data = {
            "Location": "vsphere-automation",
            "CustomerName": environment_name,
            "Timezone": "UTC",
            "InstallationType": installation_type,
            "EnvironmentPool": None,
            "Components": json.loads(JsonUtils.object_to_json(obj=system_components, null_sensitive=True))
        }

        content = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.POST,
                                                  url=url,
                                                  body=data,
                                                  expected_status_code=200)
        env_id = content.get('id')
        return env_id

    @staticmethod
    @allure.step("Wait until environment get deploy status")
    def wait_for_system_component_deploy_status(env_id: str,
                                                timeout: int = 30 * 60,
                                                sleep_interval=30):
        url = f'{third_party_details.ENVIRONMENT_SERVICE_URL}/api/v1/fedr/environment?environment_id={env_id}'

        is_ready = False
        start_time = time.time()

        while not is_ready and time.time() - start_time < start_time:
            content = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                      url=url,
                                                      expected_status_code=200)

            if 'returncode' in content.keys() is not None or 'stderr' in content.keys():
                message = json.dumps(content, indent=4)
                Reporter.attach_str_as_file(file_name="Deployment error description", file_content=message)
                assert False, f"Failed to deploy via environment service\r\n {message}"

            if content.get('ErrorDescription') is not None:
                message = content.get('ErrorDescription')
                Reporter.attach_str_as_file(file_name="Deployment error description", file_content=message)
                assert False, f"Failed to deploy via environment service\r\n {message}"

            is_ready = content.get('Ready')
            if not is_ready:
                time.sleep(sleep_interval)

        assert is_ready, f"the environment is not ready within {timeout}"

    @staticmethod
    @allure.step('Get environment details')
    def get_system_components_deploy_info(env_id: str) -> DeployedEnvInfo | None:
        url = f'{third_party_details.ENVIRONMENT_SERVICE_URL}/api/v1/fedr/environment?environment_id={env_id}'
        content = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                  url=url,
                                                  expected_status_code=200)
        if content.get('Ready') is False:
            return None

        return DeployedEnvInfo(env_id=content.get('Id'),
                               components_created=content.get('ComponentsCreated'),
                               registration_password=content.get('RegistrationPassword'),
                               admin_user=content.get('AdminUser'),
                               admin_password=content.get('AdminPassword'),
                               rest_api_user=content.get('RestAPIUser'),
                               rest_api_password=content.get('RestAPIPassword'),
                               location=content.get('Location'),
                               customer_name=content.get('CustomerName'),
                               timezone=content.get('Timezone'),
                               installation_type=content.get('InstallationType'),
                               environment_pool=content.get('EnvironmentPool'),
                               error_description=content.get('ErrorDescription'))

    @staticmethod
    @allure.step('Delete environment')
    def delete_env_external_service(env_ids: List[str]):
        url = f'{third_party_details.ENVIRONMENT_SERVICE_URL}/api/v1/fedr/environment'
        data = {
            "ids": [{"id": env_id} for env_id in env_ids]
        }
        HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.DELETE,
                                        url=url,
                                        body=data,
                                        expected_status_code=200)

    @staticmethod
    @allure.step('Deploy machine with collector')
    def deploy_vm_with_collector(vsphere_cluster_handler: VsphereClusterHandler,
                                 aggregator_ip: str,
                                 registration_password: str,
                                 machine_name: str,
                                 version: str,
                                 collector_template_name: AutomationVmTemplates,
                                 organization: str = "Default",
                                 raise_exception_on_failure: bool = True,
                                 time_to_wait_before_create_new_vm: int = 0):

        new_vm = None
        collector = None

        try:
            time.sleep(time_to_wait_before_create_new_vm)
            new_vm = vsphere_cluster_handler.clone_vm_from_template(
                vm_template=collector_template_name,
                desired_vm_name=machine_name,
                wait_until_machine_get_ip=True)
        except Exception as e:
            if raise_exception_on_failure:
                raise e

            else:
                return f"Failed to create VM with the name: {machine_name} from the template: {collector_template_name.value}\n original exception is: {e}"

        try:
            if 'win' in collector_template_name.name.lower():
                encrypted_connection = True
                if 'win7' in collector_template_name.name.lower():
                    encrypted_connection = False

                collector = WindowsCollector(host_ip=new_vm.guest.ipAddress,
                                             user_name=sut_details.win_user_name,
                                             password=sut_details.win_password)
                collector.os_station.rename_hostname(host_name=StringUtils.generate_random_string(5))

            elif 'linux' in collector_template_name.name.lower():

                collector = LinuxCollector(host_ip=new_vm.guest.ipAddress,
                                           user_name=sut_details.linux_user_name,
                                           password=sut_details.linux_password)

                # if snapshot with the name "clean_os" does not exist, create it before collector installation
                if not collector.os_station.vm_operations.is_snapshot_name_exist(
                        snapshot_name=collector.os_station.vm_operations.CLEAN_OS_SNAPSHOT_NAME):
                    collector.os_station.vm_operations.snapshot_create(
                        snapshot_name=collector.os_station.vm_operations.CLEAN_OS_SNAPSHOT_NAME,
                        memory=True)

            collector.install_collector(version=version,
                                        aggregator_ip=aggregator_ip,
                                        registration_password=registration_password,
                                        organization=organization)
        except Exception as e:
            if raise_exception_on_failure:
                raise e
            else:
                return f"Failed to install version: {version} on {machine_name} with the IP: {new_vm.guest.ipAddress} \n original exception is: {e}"

        return new_vm

    @staticmethod
    @allure.step("Creation of system component {component_type}")
    def deploy_system_component_from_template(
            vsphere_cluster_handler: VsphereClusterHandler,
            component_type: ComponentType,
            desired_component_name: str,
            desired_version: str,
            management_ip: str = None,
            management_registration_password: str = None,
            aggregator_ip: str = None) -> FortiEdrLinuxStation:
        """This function creates a FortiEdr component from a template and adds it to an existing management.
        When creating a new component it will return a new component object.

        :param vsphere_cluster_handler: VsphereClusterHandler type needed for this component to be created from the template in the cluster.
        :param component_type: ComponentType of the desired component to create.
        :param desired_component_name: Components name to be created which will be used also as hostname, suffix '_{component_type.name}' will be added.
        :param desired_version: Version of the component to be created, example 5.0.3.303.
        :param management_ip: Management IP address, defaults to None which uses from sut_details.
        :param management_registration_password: Organization registration password, defaults to None which uses from sut_details.
        :param aggregator_ip: Aggregator IP adddress, defaults to None if used with both management setup.
        :return: FortiEdrLinuxStation type object of a created component.
        """

        desired_name_component = f"{desired_component_name}_{component_type.name}"
        current_date = datetime.datetime.fromisoformat('2011-11-04').date().today()
        current_time = datetime.datetime.now().time().strftime("%H:%M")
        shared_drive_path = f'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\\{desired_version}'
        installer_file_name = f'FortiEDRInstaller_{desired_version}.x'

        # This condition is for Both setup
        if aggregator_ip is None:
            aggregator_ip = sut_details.management_host

        linux_station = vsphere_cluster_handler.clone_vm_from_template(
            vm_template=AutomationVmTemplates.CENTOS7_SYSTEM_COMPONENT_TEMPLATE,
            desired_vm_name=desired_name_component,
            wait_until_machine_get_ip=True)

        linux_station = LinuxStation(
            host_ip=linux_station.guest.ipAddress,
            user_name=sut_details.linux_user_name,
            password=sut_details.linux_password)

        path = linux_station.copy_files_from_shared_folder(
            target_path_in_local_machine='/home/user1',
            shared_drive_path=shared_drive_path,
            shared_drive_user_name=third_party_details.USER_NAME,
            shared_drive_password=third_party_details.PASSWORD,
            files_to_copy=[installer_file_name])

        linux_station.execute_cmd(fr"/{path}/{installer_file_name}")
        linux_station.reboot()
        linux_station.wait_until_machine_is_reachable(timeout=300)

        config_cmd = None
        result = None

        match component_type:
            case ComponentType.AGGREGATOR:
                config_cmd = _get_aggregator_config_cmd(
                    desired_hostname=desired_name_component,
                    date_time=current_time,
                    date_date=str(current_date),
                    management_host_ip=management_ip,
                    management_registration_password=management_registration_password)

            case ComponentType.CORE:
                config_cmd = _get_core_config_cmd(
                    desired_hostname=desired_name_component,
                    date_time=current_time,
                    date_date=str(current_date),
                    core_external_ip_address=linux_station.host_ip,
                    registration_password=management_registration_password,
                    aggregator_ip=aggregator_ip)

            # TODO: Implement returning of the management.manager object
            case ComponentType.MANAGEMENT:
                config_cmd = _get_management_config_cmd(
                    desired_hostname=desired_name_component,
                    date_time=current_time,
                    date_date=str(current_date))

            # TODO: Implement returning of the management.both object
            case ComponentType.BOTH:
                config_cmd = _get_management_config_cmd(
                    desired_hostname=desired_name_component,
                    date_time=current_time,
                    date_date=str(current_date),
                    both=True)

        result = linux_station.execute_cmd(cmd=config_cmd,
                                           return_output=True,
                                           fail_on_err=True,
                                           timeout=10 * 60,
                                           attach_output_to_report=True)

        if "failed" in result.lower():
            forti_edr_log = linux_station.get_file_content(rf'/var/log/FortiEDR/FortiEDR.log')
            assert False, f"{component_type.name} component configuration failure. '{desired_name_component}'.\n {forti_edr_log}"

        match component_type:
            case ComponentType.AGGREGATOR:
                return Aggregator(host_ip=linux_station.host_ip,
                                  ssh_password=sut_details.linux_password,
                                  ssh_user_name=sut_details.linux_user_name,
                                  aggregator_details=None)

            case ComponentType.CORE:
                return Core(host_ip=linux_station.host_ip,
                            ssh_password=sut_details.linux_password,
                            ssh_user_name=sut_details.linux_user_name,
                            core_details=None)

    @staticmethod
    @allure.step("Add random collector to organization: {organization}")
    def add_random_collector_to_setup_from_collectors_pool(vsphere_cluster_handler: VsphereClusterHandler,
                                                           clean_vms_list: [CleanVMsReadyForCollectorInstallation],
                                                           version: str,
                                                           aggregator_ip: str,
                                                           registration_password: str,
                                                           organization: str,
                                                           timeout=15 * 60):

        if clean_vms_list is None or len(clean_vms_list) == 0:
            raise Exception("Can not choose random machine since the list provided is empty or None")

        start_time = time.time()
        while time.time() - start_time < timeout:

            for vm_name in clean_vms_list:
                vm_ops = vsphere_cluster_handler.get_specific_vm_from_cluster(
                    vm_search_type=VmSearchTypeEnum.VM_NAME,
                    txt_to_search=vm_name.value)

                if vm_ops is None:
                    continue

                elif vm_ops.is_power_on():
                    # if already in use
                    continue
                else:
                    try:
                        # first indication that not in use
                        if _is_vm_free_to_use(vm_ops=vm_ops, collector_vm=vm_name):

                            # inside "add_specific_collector_to_setup_from_collectors_pool" method logic,
                            # we are checking if machine is powered off - if so, allocating it
                            # will throw exception that it's already allocated, and will continue to next candidate
                            collector = EnvironmentCreationHandler.add_specific_collector_to_setup_from_collectors_pool(
                                vsphere_cluster_handler=vsphere_cluster_handler,
                                vm_name=vm_name,
                                version=version,
                                aggregator_ip=aggregator_ip,
                                registration_password=registration_password,
                                organization=organization,
                                max_timeout=0)

                            return collector
                    except:
                        continue

    @staticmethod
    @allure.step("Add specific collector {vm_name} to organization: {organization}")
    def add_specific_collector_to_setup_from_collectors_pool(vsphere_cluster_handler: VsphereClusterHandler,
                                                             vm_name: CleanVMsReadyForCollectorInstallation,
                                                             version: str,
                                                             aggregator_ip: str,
                                                             registration_password: str,
                                                             organization: str,
                                                             max_timeout: int = 15*60) -> WindowsCollector | LinuxCollector:

        vsphere_machine_operations = vsphere_cluster_handler.get_specific_vm_from_cluster(
            vm_search_type=VmSearchTypeEnum.VM_NAME,
            txt_to_search=vm_name.value)

        if vsphere_machine_operations is None:
            assert False, f"Can not find machine with the name {vm_name.value} in vsphere"

        if vsphere_machine_operations.is_power_on():
            start_time = time.time()
            while vsphere_machine_operations.is_power_on() and time.time() - start_time < max_timeout:
                time.sleep(30)

            assert vsphere_machine_operations.is_power_off(), f"Can not allocate {vm_name.value} since it's in use"

        # double check lock
        # check if vm free to use (is power off and name as in enum)
        # random wait - if already allocated by someone else, renaming takes few millis while power on take ~ 3 seconds
        # after allocating and powering on, return the name as it was
        if _is_vm_free_to_use(vm_ops=vsphere_machine_operations, collector_vm=vm_name):
            time.sleep(random.randint(1, 4))
            if _is_vm_free_to_use(vm_ops=vsphere_machine_operations, collector_vm=vm_name):
                vsphere_machine_operations.rename_machine_in_vsphere(f"{EnvironmentCreationHandler.BUSY_VM_COLLECTOR}{vsphere_machine_operations.vm_obj.name}")
                vsphere_machine_operations.power_on()

            # wait for ip appear
            start_time = time.time()
            get_ip_timeout = 2 * 60
            while time.time() - start_time < get_ip_timeout and vsphere_machine_operations.vm_obj.guest.ipAddress is None:
                time.sleep(1)

            if vsphere_machine_operations.vm_obj.guest.ipAddress is None:
                vsphere_machine_operations.rename_machine_in_vsphere(new_name=vm_name.value)
                vsphere_machine_operations.power_off()
                assert False, f"VM did not get IP within timeout of {get_ip_timeout}"

        collector = None

        try:
            if 'win' in vm_name.value.lower():
                collector = WindowsCollector(host_ip=vsphere_machine_operations.vm_obj.guest.ipAddress,
                                             user_name=sut_details.win_user_name,
                                             password=sut_details.win_password)

            elif 'linux' in vm_name.value.lower():
                collector = LinuxCollector(host_ip=vsphere_machine_operations.vm_obj.guest.ipAddress,
                                           user_name=sut_details.win_user_name,
                                           password=sut_details.win_password)

            else:
                raise Exception(f"Can not decide if {vm_name.value} is a windows or linux OS so can not proceed with the installation")

            if collector.is_agent_installed():
                assert False, "Can not install collector since there is already installed collector on this system"

            if _is_vm_free_to_use(vm_ops=vsphere_machine_operations, collector_vm=vm_name):
                assert False, "VM is not ready to use since it's busy"


            # if snapshot with the name "clean_os" does not exist, create it before collector installation
            if not collector.os_station.vm_operations.is_snapshot_name_exist(
                    snapshot_name=collector.os_station.vm_operations.CLEAN_OS_SNAPSHOT_NAME):
                collector.os_station.vm_operations.snapshot_create(
                    snapshot_name=collector.os_station.vm_operations.CLEAN_OS_SNAPSHOT_NAME,
                    memory=True)

            collector.install_collector(version=version,
                                        aggregator_ip=aggregator_ip,
                                        registration_password=registration_password,
                                        organization=organization)

            return collector

        except Exception as e:
            vsphere_machine_operations.rename_machine_in_vsphere(vm_name.value)
            vsphere_machine_operations.revert_to_root_snapshot()
            vsphere_machine_operations.power_off()
            raise e



if __name__ == "__main__":
    import infra.vpshere.vsphere_cluster_details
    import sut_details

    vspere_details = infra.vpshere.vsphere_cluster_details.ENSILO_VCSA_40
    vsphere_handler = infra.vpshere.vsphere_cluster_handler.VsphereClusterHandler(vspere_details)
    date_random = random.random()
    # management = mgmt.instance()

    vm_aggregator = EnvironmentCreationHandler.deploy_system_component_from_template(
        vsphere_cluster_handler=vsphere_handler,
        component_type=ComponentType.AGGREGATOR,
        desired_component_name=f'test_deployment_component-{date_random}',
        desired_version='5.0.3.678',
        management_ip=sut_details.management_host,
        management_registration_password=sut_details.management_registration_password,
        aggregator_ip=None)

    vm_core = EnvironmentCreationHandler.deploy_system_component_from_template(
        vsphere_cluster_handler=vsphere_handler,
        component_type=ComponentType.CORE,
        desired_component_name=f'test_deployment_component-{date_random}',
        desired_version='5.0.3.678',
        management_ip=sut_details.management_host,
        management_registration_password=sut_details.management_registration_password,
        aggregator_ip=vm_aggregator.host_ip)

    vm_aggregator.vm_operations.remove_vm()
    vm_core.vm_operations.remove_vm()

    print("Finished...")