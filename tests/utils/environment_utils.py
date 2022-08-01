import logging
import random
from contextlib import contextmanager
from typing import List, Dict

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.enums import CleanVMsReadyForCollectorInstallation, CollectorTypes
from infra.environment_creation.environment_creation_handler import EnvironmentCreationHandler
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.vpshere.vsphere_cluster_details import ENSILO_VCSA_40
from infra.vpshere.vsphere_cluster_handler import VsphereClusterHandler
from tests.conftest import _wait_util_rest_collector_appear, _find_rest_collector
from tests.utils.collector_utils import CollectorUtils
import concurrent.futures
logger = logging.getLogger(__name__)


def _get_clean_vms_list_according_to_collector_type(collector_type: CollectorTypes) -> List[CleanVMsReadyForCollectorInstallation]:
    clean_vms_list = []

    match collector_type:
        case CollectorTypes.WINDOWS_11_64:
            clean_vms_list = [CleanVMsReadyForCollectorInstallation.WIN_11_64_1,
                              CleanVMsReadyForCollectorInstallation.WIN_11_64_2,
                              CleanVMsReadyForCollectorInstallation.WIN_11_64_3]

        case CollectorTypes.WINDOWS_10_64:
            clean_vms_list = [CleanVMsReadyForCollectorInstallation.WIN_10_64_1,
                              CleanVMsReadyForCollectorInstallation.WIN_10_64_2,
                              CleanVMsReadyForCollectorInstallation.WIN_10_64_3]

        case CollectorTypes.WINDOWS_10_32:
            clean_vms_list = [CleanVMsReadyForCollectorInstallation.WIN_10_32_1]

        case CollectorTypes.WINDOWS_8_64:
            clean_vms_list = []

        case CollectorTypes.WINDOWS_8_32:
            clean_vms_list = []

        case CollectorTypes.WINDOWS_7_64:
            clean_vms_list = []

        case CollectorTypes.WINDOWS_7_32:
            clean_vms_list = []

        case CollectorTypes.WIN_SERVER_2019:
            clean_vms_list = CleanVMsReadyForCollectorInstallation.WIN_SRV_2019_64_1

        case CollectorTypes.WIN_SERVER_2016:
            clean_vms_list = []

        case CollectorTypes.LINUX_CENTOS_8:
            clean_vms_list = []

        case CollectorTypes.LINUX_CENTOS_7:
            clean_vms_list = []

        case CollectorTypes.LINUX_CENTOS_6:
            clean_vms_list = []

        case CollectorTypes.LINUX_UBUNTU_20:
            clean_vms_list = []

        case _:
            raise Exception(f"Collector of the type: {collector_type} is not supported")

    return clean_vms_list


@contextmanager
def add_collectors_from_pool(management: Management,
                             desired_version: str,
                             aggregator_ip: str,
                             organization: str,
                             registration_password: str,
                             desired_collectors_dict: Dict[CollectorTypes, int]) -> List[CollectorAgent]:
    exception = None
    vspere_details = ENSILO_VCSA_40
    vsphere_handler = VsphereClusterHandler(vspere_details)

    deployed_collectors = []
    args_list = []

    try:

        with allure.step("Going to add collector from collectors pool"):

            for desired_collector_type, amount in desired_collectors_dict.items():
                clean_vms_list = _get_clean_vms_list_according_to_collector_type(collector_type=desired_collector_type)

                if len(clean_vms_list) == 0 or clean_vms_list is None:
                    raise Exception(f"There is no vms of the type {desired_collector_type} in pool, not supported")

                if amount > len(clean_vms_list):
                    raise Exception(f"Can not add {amount} collectors of the type: {desired_collector_type}"
                                    f"since there are only {len(clean_vms_list)} vms of this type in collectors pool")

                for i in range(amount):
                    time_to_wait_before_method = random.randint(1, 10)
                    args = (vsphere_handler, clean_vms_list, desired_version, aggregator_ip, registration_password, organization, time_to_wait_before_method)
                    args_list.append(args)

            with allure.step("Add collectors from pool in parallel"):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [executor.submit(EnvironmentCreationHandler.add_random_collector_to_setup_from_collectors_pool, *param) for param in args_list]
                    deployed_collectors = [f.result() for f in futures]

            with allure.step("Wait until all collectors appear in management"):
                for deployed_collector in deployed_collectors:
                    rest_collector = _wait_util_rest_collector_appear(host_ip=deployed_collector.host_ip,
                                                                      tenant=management.tenant,
                                                                      timeout=120)

                    rest_collector.wait_until_running()

        yield deployed_collectors

    except Exception as original_exception:
        logger.info(f"Test Failed ! got: \n {original_exception} \n Now will try to release collectors back to pool")
        exception = original_exception
        raise original_exception

    finally:

        exceptions_raised_during_cleanup = []

        with allure.step("Release collector back to collectors pool"):

            for single_collector in deployed_collectors:

                with allure.step(f"Release {single_collector} back to pool"):
                    single_collector.os_station.vm_operations.revert_to_root_snapshot()
                    original_name = single_collector.os_station.vm_operations.vm_obj.name.replace(
                        EnvironmentCreationHandler.BUSY_VM_COLLECTOR, '')

                    single_collector.os_station.vm_operations.rename_machine_in_vsphere(new_name=original_name)
                    single_collector.os_station.vm_operations.power_off()
                    Reporter.report(f"{single_collector} released successfully")

                    try:
                        rest_collector = _find_rest_collector(host_ip=single_collector.host_ip, tenant=management.tenant)
                        # CollectorUtils.wait_until_rest_collector_is_off(rest_collector=rest_collector)
                        rest_collector.delete()

                    except Exception as e:
                        exceptions_raised_during_cleanup.append(e)

        if exception is not None:
            raise exception

        if len(exceptions_raised_during_cleanup) > 0:
            for single_exception in exceptions_raised_during_cleanup:
                Reporter.report(message=f"Exception raised during cleanup: {single_exception}", logger_func=logger.info)

            assert False, "Multiple exception raised during cleanup, check the report"
