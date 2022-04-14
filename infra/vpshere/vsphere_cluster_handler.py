import atexit
import time
from enum import Enum

import allure
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim

from infra.allure_report_handler.reporter import Reporter
from infra.vpshere.vsphere_cluster_details import ClusterDetails
from infra.enums import CollectorTemplateNames
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
        self._container_view = None

    @property
    def cluster_details(self):
        return self._cluster_details

    @property
    def service_instance(self):
        if self._service_instance is not None:
            return self._service_instance
        else:
            raise Exception("Service instance not initiated.")

    def _get_resource_pool_object(self) -> object:
        resourse_pool = self._get_all_resource_pools_objects()

        if self.cluster_details.cluster_resources_pool[0] in resourse_pool:
            return resourse_pool[self.cluster_details.cluster_resources_pool[0]]
        else:
            return None

    def _get_all_folders_objects(self) -> dict:
        folders_dict = {}

        folders = self._get_vsphere_objects(
                content=self.service_instance.content,
                vim_type=[vim.Folder]
            )
        for folder in folders:
            folders_dict[folder.name] = folder

        return folders_dict

    def _get_all_resource_pools_objects(self) -> dict:
        resource_pools_dict = {}

        resource_pools = self._get_vsphere_objects(
                content=self.service_instance.content,
                vim_type=[vim.ResourcePool]
            )
        for resource_pool in resource_pools:
            resource_pools_dict[resource_pool.name] = resource_pool

        return resource_pools_dict

    def create_vm(self, vm_template: CollectorTemplateNames, desired_vm_name: str):

        vm_to_clone_from_obj = self.get_specific_vm_from_cluster(vm_search_type=VmSearchTypeEnum.VM_NAME, txt_to_search=vm_template.value)
        resource_pool = self._get_resource_pool_object()
        folders_dict = self._get_all_folders_objects()

        if vm_to_clone_from_obj is not None:
            desired_vm_name = f"{desired_vm_name}_{int(time.time())}"

            created_vm_obj = vm_to_clone_from_obj.clone_vm_by_name(
                vm_template_object=vm_to_clone_from_obj.vm_obj,
                resource_pool_object=resource_pool,
                folder_object=folders_dict['vm'],
                power_on=True,
                new_vm_name=desired_vm_name
            )
            return created_vm_obj
        else:
            raise Exception(f"Machine\Template with the name: {desired_vm_name} does not exist, can not clone")

    @allure.step("Connect to vsphere")
    def connect_to_vsphere(self, user_name: str = USER_NAME_DOMAIN, password: str = PASSWORD):
        try:
            self._service_instance = SmartConnectNoSSL(
                host=self.cluster_details.cluster_vhost,
                user=user_name,
                pwd=password
            )
            if self._service_instance is not None:
                self._container_view = self.service_instance.content.viewManager.CreateContainerView
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

        if vm_obj is None:
            Reporter.report(f"VM is not found under {self._cluster_details.cluster_name}")
            return None

        if ip_address == vm_obj.guest.ipAddress and vm_obj.guest.ipAddress and vm_obj.configStatus == 'green':
            Reporter.report(f"IP address '{ip_address}' of a collector {vm_obj.name} found. ")
        else:
            raise Exception("vm object is found but there is no IP address or machine is powered off")

        return vm_obj

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

        if vm_obj is None:
            return None

        vsphere_operations = VsphereMachineOperations(service_instance=self._service_instance,
                                                      vm_obj=vm_obj)

        return vsphere_operations

    def _get_vsphere_objects(self, content, vim_type, folder=None, recurse=True):
        """
            Search the managed object for the name and type specified.

            Sample Usage:
                get_obj(content, [vim.Datastore], "Datastore Name")
        """
        if not folder:
            folder = content.rootFolder

        obj = {}
        container = content.viewManager.CreateContainerView(folder, vim_type, recurse)

        for managed_object_ref in container.view:
            obj[managed_object_ref] = managed_object_ref.name

        container.Destroy()
        return obj

    def _get_obj(self, content, vim_type, name, folder=None, recurse=True):
        """
        Retrieves the managed object for the name and type specified
        Throws an exception if of not found.

        Sample Usage:
            get_obj(content, [vim.Datastore], "Datastore Name")
        """
        obj = self._search_for_obj(content, vim_type, name, folder, recurse)
        if not obj:
            raise RuntimeError("Managed Object " + name + " not found.")
        return obj

    def _search_for_obj(self,content, vim_type, name, folder=None, recurse=True):
        """
        Search the managed object for the name and type specified

        Sample Usage:
            get_obj(content, [vim.Datastore], "Datastore Name")
        """
        if folder is None:
            folder = content.rootFolder

        obj = None
        container = content.viewManager.CreateContainerView(folder, vim_type, recurse)

        for managed_object_ref in container.view:
            if managed_object_ref.name == name:
                obj = managed_object_ref
                break
        container.Destroy()
        return obj


if __name__ == '__main__':
    from infra.vpshere import vsphere_cluster_details, vsphere_utils

    cluster_details = vsphere_cluster_details.ENSILO_VCSA_40
    vsphere_cluster_handler = VsphereClusterHandler(cluster_details=cluster_details)

    # vsphere_cluster_handler.get_specific_vm_from_cluster(vm_search_type=VmSearchTypeEnum.VM_NAME,
    #                                                      txt_to_search=CollectorTemplateNames.WIN10_X64.value
    #                                                      )

    created_vm = vsphere_cluster_handler.create_vm(
        vm_template=CollectorTemplateNames.WIN10_X64,
        desired_vm_name="dima_colletor10x64"
    )

    created_vm_ip = created_vm.guest.ipAddress

    # vm_ops.power_off()
    # vm_ops.snapshot_rename(vm_ops.vm_obj.snapshot.currentSnapshot, 'dima test new name')
    # vm_ops.power_on()
    # vm_ops.remove_all_snapshots()
    # vm_ops.snapshot_revert_by_name(snapshot_name='dima test')

    print("END...")
