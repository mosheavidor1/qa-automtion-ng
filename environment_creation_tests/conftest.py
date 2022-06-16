import random
from datetime import date
from typing import List
import concurrent.futures

import allure
import pytest

from environment_creation_tests import desired_env_details
from forti_edr_versions_service_handler.forti_edr_versions_service_handler import FortiEdrVersionsServiceHandler
from infra.allure_report_handler.reporter import Reporter
from infra.containers.environment_creation_containers import MachineType, EnvironmentSystemComponent, DeployedEnvInfo
from infra.enums import ComponentType, AutomationVmTemplates
from infra.environment_creation.environment_creation_handler import EnvironmentCreationHandler
from infra.utils.utils import StringUtils
from infra.vpshere import vsphere_cluster_details
from infra.vpshere.vsphere_cluster_handler import VsphereClusterHandler


def get_collector_latest_version(version: str, last_versions_dict: dict, collector_template_name: AutomationVmTemplates):
    build = StringUtils.get_txt_by_regex(text=version, regex="\d+.\d+.\d+.(\w+)", group=1)
    base_version = StringUtils.get_txt_by_regex(text=version, regex="(\d+.\d+.\d+).\w+", group=1)
    desired_version = None

    if build.isdigit():
        desired_version = version

    if build == 'x':
        key_to_use = None
        match collector_template_name:
            case AutomationVmTemplates.WIN_11X64 | \
                 AutomationVmTemplates.WIN10_X64 | \
                 AutomationVmTemplates.WIN81_X64 | \
                 AutomationVmTemplates.WIN7_X64 | \
                 AutomationVmTemplates.WIN_SERV_2022 | \
                 AutomationVmTemplates.WIN_SERV_2020 | \
                 AutomationVmTemplates.WIN_SERV_2019 | \
                 AutomationVmTemplates.WIN_SERV_2016 | \
                 AutomationVmTemplates.WIN_SERV_2012:
                key_to_use = 'windows_64_collector'

            case AutomationVmTemplates.WIN10_X32 | AutomationVmTemplates.WIN81_X32 | AutomationVmTemplates.WIN7_X86:
                key_to_use = 'windows_32_collector'

            case AutomationVmTemplates.LINUX_CENTOS_6:
                key_to_use = 'centos_6_collector'

            case AutomationVmTemplates.LINUX_CENTOS_7:
                key_to_use = 'centos_7_collector'

            case AutomationVmTemplates.LINUX_CENTOS_8:
                key_to_use = 'centos_8_collector'

            case AutomationVmTemplates.LINUX_UBUNTU_20:
                key_to_use = 'ubuntu_20_collector'

            case AutomationVmTemplates.LINUX_UBUNTU_18:
                key_to_use = 'ubuntu_18_collector'

            case AutomationVmTemplates.LINUX_UBUNTU_16:
                key_to_use = 'ubuntu_16_collector'

            case AutomationVmTemplates.LINUX_AMAZON:
                key_to_use = 'amazonlinux'

            case AutomationVmTemplates.LINUX_SUSE:
                key_to_use = 'openSUSE_collector'

            case AutomationVmTemplates.LINUX_ORACLE_83 | \
                 AutomationVmTemplates.LINUX_ORACLE_82 | \
                 AutomationVmTemplates.LINUX_ORACLE_81 | \
                 AutomationVmTemplates.LINUX_ORACLE_80:
                key_to_use = 'oracle_8_collector'

            case AutomationVmTemplates.LINUX_ORACLE_77:
                key_to_use = 'oracle_7_collector'

        desired_version = last_versions_dict.get(base_version).get(key_to_use)

    assert desired_version is not None, f"can not find latest version for {collector_template_name.value}"

    Reporter.report(f"Desired version for {collector_template_name.value} is: {desired_version}")

    return desired_version


def get_non_collector_latest_version(version: str, last_versions_dict: dict, component_type: ComponentType):
    build = StringUtils.get_txt_by_regex(text=version, regex="\d+.\d+.\d+.(\w+)", group=1)
    base_version = StringUtils.get_txt_by_regex(text=version, regex="(\d+.\d+.\d+).\w+", group=1)
    desired_version = None

    if build is None:
        assert False, f"{version} - Incorrect version pattern, example of correct patterns: 5.2.0.1 or 5.2.0.x"

    if build.isdigit():
        desired_version = version

    if build == 'x':

        key_to_use = None
        match component_type:
            case ComponentType.MANAGEMENT:
                key_to_use = 'management'
            case ComponentType.AGGREGATOR:
                key_to_use = 'aggregator'
            case ComponentType.CORE:
                key_to_use = 'core'

        desired_version = last_versions_dict.get(base_version).get(key_to_use)

    assert desired_version is not None, f"can not find latest version for {component_type.value}"

    Reporter.report(f"Desired version for {component_type.value} is: {desired_version}")

    return desired_version


def get_base_versions_of_all_sys_components_as_dict():
    base_versions_dict = {}
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.management_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.aggregator_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.core_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.windows_collector_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.linux_collector_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    return base_versions_dict


@allure.step("Extract latest versions")
def get_latest_versions_of_all_base_versions_dict(base_versions_dict: dict):
    last_versions_dict = {}
    for key in base_versions_dict.keys():
        tmp = FortiEdrVersionsServiceHandler.get_latest_versions(base_version=key)
        last_versions_dict[key] = tmp

    return last_versions_dict


@allure.step("Deploy system components")
def deploy_system_components(env_name='automation_env'):
    base_versions_dict = get_base_versions_of_all_sys_components_as_dict()
    latest_versions_dict = get_latest_versions_of_all_base_versions_dict(base_versions_dict=base_versions_dict)

    management_ver = get_non_collector_latest_version(version=desired_env_details.management_version,
                                                      last_versions_dict=latest_versions_dict,
                                                      component_type=ComponentType.MANAGEMENT)
    aggregator_ver = get_non_collector_latest_version(version=desired_env_details.aggregator_version,
                                                      last_versions_dict=latest_versions_dict,
                                                      component_type=ComponentType.AGGREGATOR)
    core_ver = get_non_collector_latest_version(version=desired_env_details.core_version,
                                                last_versions_dict=latest_versions_dict,
                                                component_type=ComponentType.CORE)

    machine_type = MachineType(cpu_count=4,
                               memory_limit=16000,
                               disk_size=40000)

    sys_comp_list = []
    if desired_env_details.management_and_aggregator_deployment_architecture == 'both':
        manager_aggr = EnvironmentSystemComponent(component_type=ComponentType.BOTH,
                                                  component_version=management_ver,
                                                  machine_type=machine_type)
        sys_comp_list.append(manager_aggr)

    elif desired_env_details.management_and_aggregator_deployment_architecture == 'separate':
        manager = EnvironmentSystemComponent(component_type=ComponentType.MANAGEMENT,
                                             component_version=management_ver,
                                             machine_type=machine_type)
        sys_comp_list.append(manager)

        for i in range(desired_env_details.aggregator_version):
            aggr = EnvironmentSystemComponent(component_type=ComponentType.AGGREGATOR,
                                              component_version=aggregator_ver,
                                              machine_type=machine_type)
            sys_comp_list.append(aggr)
    else:
        assert False, f"Unknown deployment architecture: {desired_env_details.management_and_aggregator_deployment_architecture}"

    for i in range(desired_env_details.cores_amount):
        core = EnvironmentSystemComponent(component_type=ComponentType.CORE,
                                          component_version=core_ver,
                                          machine_type=machine_type)
        sys_comp_list.append(core)

    env_id = EnvironmentCreationHandler.deploy_system_components_external_service(
        environment_name=env_name.replace(" ", "_"),
        system_components=sys_comp_list,
        installation_type='qa')

    EnvironmentCreationHandler.wait_for_system_component_deploy_status(env_id=env_id,
                                                                       timeout=30 * 60,
                                                                       sleep_interval=60)

    deployed_env_info = EnvironmentCreationHandler.get_system_components_deploy_info(env_id=env_id)
    return deployed_env_info


def get_list_of_desired_collectors() -> List[AutomationVmTemplates]:
    deployment_list = []
    deployment_list += [AutomationVmTemplates.WIN_11X64 for i in range(desired_env_details.windows_11_64_bit)]
    deployment_list += [AutomationVmTemplates.WIN10_X64 for i in range(desired_env_details.windows_10_64_bit)]
    deployment_list += [AutomationVmTemplates.WIN10_X32 for i in range(desired_env_details.windows_10_32_bit)]
    deployment_list += [AutomationVmTemplates.WIN81_X64 for i in range(desired_env_details.windows_8_64_bit)]
    deployment_list += [AutomationVmTemplates.WIN81_X32 for i in range(desired_env_details.windows_8_32_bit)]
    deployment_list += [AutomationVmTemplates.WIN7_X64 for i in range(desired_env_details.windows_7_64_bit)]
    deployment_list += [AutomationVmTemplates.WIN7_X86 for i in range(desired_env_details.windows_7_32_bit)]
    # deployment_list += [CollectorTemplateNames.WIN_SERV_2022 for i in range(desired_env_details.)]
    # deployment_list += [CollectorTemplateNames.WIN_SERV_2020 for i in range(desired_env_details.)]
    deployment_list += [AutomationVmTemplates.WIN_SERV_2019 for i in range(desired_env_details.windows_server_2019)]
    deployment_list += [AutomationVmTemplates.WIN_SERV_2016 for i in range(desired_env_details.windows_server_2016)]
    # deployment_list += [CollectorTemplateNames.WIN_SERV_2012 for i in range(desired_env_details.)]
    deployment_list += [AutomationVmTemplates.LINUX_CENTOS_8 for i in range(desired_env_details.centOS_8)]
    deployment_list += [AutomationVmTemplates.LINUX_CENTOS_7 for i in range(desired_env_details.centOS_7)]
    deployment_list += [AutomationVmTemplates.LINUX_CENTOS_6 for i in range(desired_env_details.centOS_6)]
    deployment_list += [AutomationVmTemplates.LINUX_UBUNTU_20 for i in range(desired_env_details.ubuntu_20)]
    deployment_list += [AutomationVmTemplates.LINUX_UBUNTU_18 for i in range(desired_env_details.ubuntu_18)]
    deployment_list += [AutomationVmTemplates.LINUX_UBUNTU_16 for i in range(desired_env_details.ubuntu_16)]
    # deployment_list += [CollectorTemplateNames.LINUX_AMAZON for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_SUSE for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_ORACLE_83 for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_ORACLE_82 for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_ORACLE_81 for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_ORACLE_80 for i in range(desired_env_details.windows_11_64_bit)]
    # deployment_list += [CollectorTemplateNames.LINUX_ORACLE_77 for i in range(desired_env_details.windows_11_64_bit)]

    return deployment_list


@allure.step('Deploy collectors')
def deploy_collectors(aggregator_ip: str,
                      registration_password: str,
                      organization: str,
                      env_name='automation_env_exp') -> dict:

    base_versions_dict = get_base_versions_of_all_sys_components_as_dict()
    latest_versions_dict = get_latest_versions_of_all_base_versions_dict(base_versions_dict=base_versions_dict)

    ret_dict = {}
    desired_collectors_list = get_list_of_desired_collectors()
    vsphere_cluster_handler = VsphereClusterHandler(cluster_details=vsphere_cluster_details.ENSILO_VCSA_40)

    args_list = []
    for template in desired_collectors_list:
        # if we want to seperate according to specific collector type (not only by OS) - write here the logic
        desired_version = None
        if 'win' in template.name.lower():
            desired_version = desired_env_details.windows_collector_version

        elif 'linux' in template.name.lower():
            desired_version = desired_env_details.linux_collector_version

        else:
            raise Exception(f"Can not determine which version to choose for: {template.name}")

        version = get_collector_latest_version(version=desired_version,
                                               last_versions_dict=latest_versions_dict,
                                               collector_template_name=template)

        raise_exception_on_failure = False
        rand_str = StringUtils.generate_random_string(length=5)  # added in case of multi-thread usage
        # curr_time = str(time.time()).replace('.', '_')
        # collector_name = f'{env_name}_{template.value}_{rand_str}_{curr_time}'
        collector_name = f'{template.value}_{rand_str}_{env_name}'
        collector_name = collector_name.replace("TEMPLATE_", "")
        collector_name = collector_name.replace(" ", "_")
        if len(collector_name) >= 80:
            collector_name = collector_name[:79]

        time_to_sleep_before_create_new_vm = random.randint(0, 60)

        args = (
            vsphere_cluster_handler, aggregator_ip, registration_password, collector_name, version, template,
            organization,
            raise_exception_on_failure, time_to_sleep_before_create_new_vm)
        args_list.append(args)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(EnvironmentCreationHandler.deploy_vm_with_collector, *param) for param in args_list]
        vm_objects = [f.result() for f in futures]

        c = 1
        for vm_obj in vm_objects:
            if isinstance(vm_obj, str):
                ret_dict[f'failure_{c}'] = vm_obj
                c += 1
            else:
                ret_dict[vm_obj.guest.ipAddress] = {
                    'host_name': vm_obj.name
                }

    return ret_dict


def get_deployed_system_component_info_by_type(deployed_env_info: DeployedEnvInfo,
                                               component_type: ComponentType):
    system_components = []
    for component_dict in deployed_env_info.components_created:
        if component_type.value == component_dict.get('ComponentType'):
            system_components.append(component_dict)

    return system_components


@pytest.fixture(scope="session")
def setup_environment():

    environment_name = desired_env_details.environment_name
    if environment_name is None:
        today = date.today()
        curr_day = today.strftime("%d-%b-%Y")
        environment_name = f'{curr_day}_automation_environment_{StringUtils.generate_random_string(4)}'

    deployed_env_info = deploy_system_components(env_name=environment_name)
    aggregator_ips = deployed_env_info.aggregator_ips
    assert len(aggregator_ips) != 0, "There is no deployed aggregators, can not proceed and deploy collectors machines"

    deployed_collectors_info = deploy_collectors(env_name=f'{environment_name}_{deployed_env_info.env_id}',
                                                 aggregator_ip=aggregator_ips[0],
                                                 registration_password=deployed_env_info.registration_password,
                                                 organization=deployed_env_info.customer_name)

    ret_dict = {
        'system_components': deployed_env_info,
        'collectors': deployed_collectors_info
    }

    yield ret_dict

    # EnvironmentCreationHandler.delete_env(env_ids=[env_id])