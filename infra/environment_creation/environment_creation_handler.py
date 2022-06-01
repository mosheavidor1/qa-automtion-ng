import json
import time
from typing import List

import allure

import sut_details
import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.containers.environment_creation_containers import EnvironmentSystemComponent, DeployedEnvInfo
from infra.enums import HttpRequestMethodsEnum, CollectorTemplateNames
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.utils.utils import JsonUtils, HttpRequesterUtils, StringUtils
from infra.vpshere.vsphere_cluster_handler import VsphereClusterHandler


class EnvironmentCreationHandler:

    @staticmethod
    @allure.step("Deploy system components using deployment service")
    def deploy_system_components(environment_name: str,
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
    def delete_env(env_ids: List[str]):
        url = f'{third_party_details.ENVIRONMENT_SERVICE_URL}/api/v1/fedr/environment'
        data = {
            "ids": [{"id": env_id} for env_id in env_ids]
        }
        HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.DELETE,
                                        url=url,
                                        body=data,
                                        expected_status_code=200)

    @staticmethod
    @allure.step('Extract latest versions from dedicated service of the base version: {base_version}')
    def get_latest_versions(base_version):
        if base_version.count('.') != 2:
            assert False, "Incorrect template of base version, insert something such as 5.1.0 (x.y.z)"

        url = f'http://{third_party_details.AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{third_party_details.LATEST_VERSIONS_SERVICE_PORT}/latest_build?base_version={base_version}'
        versions_dict = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                        url=url,
                                                        expected_status_code=200)
        return versions_dict

    @staticmethod
    @allure.step('Deploy machine with collector')
    def deploy_vm_with_collector(vsphere_cluster_handler: VsphereClusterHandler,
                                 aggregator_ip: str,
                                 registration_password: str,
                                 machine_name: str,
                                 version: str,
                                 collector_template_name: CollectorTemplateNames,
                                 organization: str = "Default",
                                 raise_exception_on_failure: bool = True,
                                 time_to_wait_before_create_new_vm: int = 0):

        new_vm = None
        collector = None

        try:
            time.sleep(time_to_wait_before_create_new_vm)
            new_vm = vsphere_cluster_handler.create_vm(
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
