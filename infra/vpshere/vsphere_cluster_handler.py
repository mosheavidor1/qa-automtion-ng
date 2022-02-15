import atexit
from enum import Enum

import allure
from pyVim.connect import SmartConnectNoSSL, Disconnect

from infra.allure_report_handler.reporter import Reporter
from infra.vpshere.vsphere_cluster_details import ClusterDetails
from infra.vpshere.vsphere_vm_operations import VsphereMachineOperations
from third_party_details import USER_NAME_DOMAIN, PASSWORD

__author__ = "Dmitry Banny"


class VmSearchTypeEnum(Enum):
    VM_NAME = 'VM_NAME'
    VM_IP_V4 = 'VM_IP_V4'


class VsphereClusterHandler(object):
    """ This class provides a connection to a Vsphere """

    def __init__(self, cluster_details: ClusterDetails):
        self._cluster_details = cluster_details
        self._service_instance = None

    @property
    def cluster_details(self):
        return self._cluster_details

    @allure.step("Connect to vsphere")
    def connect_to_vsphere(self, user_name: str = USER_NAME_DOMAIN, password: str = PASSWORD):
        try:
            self._service_instance = SmartConnectNoSSL(
                host=self.cluster_details.cluster_vhost,
                user=user_name,
                pwd=password
            )
            atexit.register(Disconnect, self._service_instance)

        except IOError as io_error:
            Reporter.report(io_error)
            return False

    @allure.step("Search for VM by name")
    def get_vm_by_name(self, vm_name: str):
        """Searching VM name in the vSphere cluster, after it found, VM object set.

        Parameters
        ----------
        vm_name : str
            VM name that you want to search in the vSphere

        Returns
        -------
        object
            Returns a VM object
        """
        for vm_obj in self._service_instance.content.rootFolder.childEntity[0].vmFolder.childEntity:
            if vm_name == vm_obj.name:
                Reporter.report(f"VM found by name: {vm_name}")
                return vm_obj

        return None

    @allure.step("Search for VM by ip")
    def search_vm_by_ip(self, ip_address: str):
        """Searching VM name in the vSphere cluster, after it found, VM object set.

        Parameters
        ----------
        ip_address : str
            IP address that you want to search in the vSphere

        Returns
        -------
        object
            Returns a VM object
        """
        vm_obj = self._service_instance.content.searchIndex.FindByIp(None, ip_address, True)

        try:
            Reporter.report(vm_obj.guest.ipAddress)
            if ip_address == vm_obj.guest.ipAddress and vm_obj.guest.ipAddress and vm_obj.configStatus == 'green':
                Reporter.report(f"IP address '{ip_address}' of a collector {vm_obj.name} found. ")
                return vm_obj
        except Exception as e:
            Reporter.report(f"IP address '{ip_address}' of a collector {vm_obj.name} not found. ")
            Reporter.report(str(e))

        return None

    @allure.step("Get a VM from the cluster")
    def get_specific_vm_from_cluster(self,
                                     vm_search_type: VmSearchTypeEnum,
                                     txt_to_search: str,
                                     user_name: str = USER_NAME_DOMAIN,
                                     password: str = PASSWORD) -> VsphereMachineOperations:
        if self._service_instance is None:
            self.connect_to_vsphere(user_name=user_name,
                                    password=password)

        if vm_search_type == VmSearchTypeEnum.VM_NAME:
            vm_obj = self.get_vm_by_name(vm_name=txt_to_search)

        elif vm_search_type == VmSearchTypeEnum.VM_IP_V4:
            vm_obj = self.search_vm_by_ip(ip_address=txt_to_search)

        else:
            raise Exception(f'Unknown vm_search_type: {vm_search_type.name}')

        vsphere_operations = VsphereMachineOperations(service_instance=self._service_instance,
                                                      vm_obj=vm_obj)

        return vsphere_operations


if __name__ == '__main__':
    cluster_details = ClusterDetails(vhost="10.51.100.120", name="Ensilo_vcsa20", resource_pools=["QA22", "QA23"], datastore_name="loc-vt22-r10-d1")
    vsphere_cluster_handler = VsphereClusterHandler(cluster_details=cluster_details)
    vm_ops = vsphere_cluster_handler.get_specific_vm_from_cluster(vm_search_type=VmSearchTypeEnum.VM_NAME, txt_to_search='dima_colletor10x64')
    vm_ops.snapshot_create(snapshot_name='dima test')
    vm_ops.snapshot_create(snapshot_name='dima test2')
    vm_ops.power_off()
    vm_ops.power_on()
    vm_ops.remove_all_snapshots()
    # vm_ops.snapshot_revert_by_name(snapshot_name='dima test')


