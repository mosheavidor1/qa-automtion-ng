import allure
import pytest

import desired_env_details
import sut_details
from infra.allure_report_handler.reporter import Reporter
from infra.containers.environment_creation_containers import MachineType, EnvironmentSystemComponent
from infra.enums import ComponentType
from infra.environment_creation.environment_creation_handler import EnvironmentCreationHandler
from infra.utils.utils import StringUtils


def get_non_collector_latest_version(version: str, last_versions_dict: dict, component_type: ComponentType):
    build = StringUtils.get_txt_by_regex(text=version, regex="\d+.\d+.\d+.(\w+)", group=1)
    base_version = StringUtils.get_txt_by_regex(text=version, regex="(\d+.\d+.\d+).\w+", group=1)
    desired_version = None

    if build is None:
        assert False, f"{version} - Incorrect version pattern, example of correct patterns: 5.2.0.1 or 5.2.0.x"

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

    if build.isdigit():
        desired_version = version

    assert desired_version is not None, "build number should be 'x' for latest version or any other number"

    Reporter.report(f"Desired version for {component_type.value} is: {desired_version}")

    return desired_version


def get_base_versions_of_all_sys_components_as_dict():
    base_versions_dict = {}
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.management_version, regex="(\d+.\d+.\d+).\w+",group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.aggregator_version, regex="(\d+.\d+.\d+).\w+",group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.core_version, regex="(\d+.\d+.\d+).\w+", group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.windows_collector_version, regex="(\d+.\d+.\d+).\w+",group=1)] = None
    base_versions_dict[StringUtils.get_txt_by_regex(text=desired_env_details.linux_collector_version, regex="(\d+.\d+.\d+).\w+",group=1)] = None
    return base_versions_dict


@allure.step("Extract latest versions")
def get_latest_versions_of_all_base_versions_dict(base_versions_dict: dict):
    last_versions_dict = {}
    for key in base_versions_dict.keys():
        tmp = EnvironmentCreationHandler.get_latest_versions(base_version=key)
        last_versions_dict[key] = tmp

    return last_versions_dict


@pytest.fixture(scope="session")
def setup_environment():
    if sut_details.management_host is None or sut_details.management_host.lower() == 'latest':

        base_versions_dict = get_base_versions_of_all_sys_components_as_dict()
        latest_versions_dict = get_latest_versions_of_all_base_versions_dict(base_versions_dict=base_versions_dict)

        management_ver = get_non_collector_latest_version(version=desired_env_details.management_version, last_versions_dict=latest_versions_dict, component_type=ComponentType.MANAGEMENT)
        aggregator_ver = get_non_collector_latest_version(version=desired_env_details.aggregator_version, last_versions_dict=latest_versions_dict, component_type=ComponentType.AGGREGATOR)
        core_ver = get_non_collector_latest_version(version=desired_env_details.core_version, last_versions_dict=latest_versions_dict, component_type=ComponentType.CORE)

        machine_type = MachineType(cpu_count=1, memory_limit=4000, disk_size=500000)

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

        env_id = EnvironmentCreationHandler.deploy_system_components(
            environment_name='automation_env_exp',
            system_components=sys_comp_list,
            installation_type='qa')

        EnvironmentCreationHandler.wait_for_system_component_deploy_status(env_id=env_id,
                                                                           timeout=30 * 60,
                                                                           sleep_interval=60)

        deployed_env_info = EnvironmentCreationHandler.get_system_components_deploy_info(env_id=env_id)

        yield deployed_env_info

        # EnvironmentCreationHandler.delete_env(env_ids=[env_id])

    else:
        yield None