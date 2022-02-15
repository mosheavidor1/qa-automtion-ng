import allure

from infra.vpshere.vsphere_cluster_details import ENSILO_VCSA_10, ENSILO_VCSA_20, ENSILO_VCSA_30, ENSILO_VCSA_40
from infra.vpshere.vsphere_cluster_handler import VmSearchTypeEnum, VsphereClusterHandler
from infra.vpshere.vsphere_vm_operations import VsphereMachineOperations
from third_party_details import USER_NAME_DOMAIN, PASSWORD


class VsphereUtils:

    @staticmethod
    @allure.step("Get specific VM from vSphere")
    def get_specific_vm_from_vsphere(vm_search_type: VmSearchTypeEnum,
                                     txt_to_search: str,
                                     user_name: str = USER_NAME_DOMAIN,
                                     password: str = PASSWORD) -> VsphereMachineOperations:
        """
        The role of this method is to search the host IP on the all vSphere clusters
        and return object that contains the operations logic such as create_snapshot, revert_to_snapshot, etc.

        :param vm_search_type:  VmSearchTypeEnum
        :param txt_to_search: txt_to_search, for example host ip or host name, depend on enum
        :param user_name: domain user name
        :param password: password to vSphere
        :return:
        """
        all_clusters_details = [ENSILO_VCSA_20, ENSILO_VCSA_10, ENSILO_VCSA_30, ENSILO_VCSA_40]

        for single_cluster_details in all_clusters_details:
            vsphere_cluster_handler = VsphereClusterHandler(cluster_details=single_cluster_details)
            vm_ops = vsphere_cluster_handler.get_specific_vm_from_cluster(vm_search_type=vm_search_type,
                                                                          txt_to_search=txt_to_search,
                                                                          user_name=user_name,
                                                                          password=password)
            if vm_ops is not None:
                return vm_ops

        return None

