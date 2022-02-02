import vsphere_details
import vsphere_operations
from third_party_details import USER_NAME, PASSWORD

__author__ = "Dmitry Banny"


class VsphereConnection(object):
    """ This class provides a connection to a Vsphere """

    def __init__(self, username=f"ensilo\\{USER_NAME}", password=PASSWORD, vm_name=None, malware=False):
        """Providing a connection information to a Vsphere is required.

        Parameters
        ----------
        password : str
            Password to connect to Vsphere
        username : str
            Username to connect to Vsphere
            Virtual machine name to use for manipulation
        malware : bool, optional
            Set to True is the environment is DENGER to other clusters , by default False
        """
        self.username: str = username
        self.password: str = password
        self.vm_name: str = vm_name
        self._malware: bool = malware
        self.vsphere_obj: object = None
        self.cluster_details: object = None

    def virtual_machine(self, cluster_name=None):
        """This function represents a VM object.

        Usage example
        ----------
        vm = VsphereConnection().cluster(vsphere_config.Ensilo_vcsa20)
        vm.snapshot_create(snapshot_name="test 1", snapshot_description="test description")

        Parameters
        ----------
        cluster_name : object
            cluster information, should be provided from a 'vsphere_config'

        Returns
        -------
        VM object
            Returns a VM object with options to manipulate the machines.
        """
        if self._malware:
            self.vsphere_obj = vsphere_operations.VsphereMachine(
                username=self.username,
                password=self.password,
                vm_name=self.vm_name,
                datastore_name=vsphere_details.Ensilo_vcsa30.cluster_datastore_name,
                datacenter_name=vsphere_details.Ensilo_vcsa30.cluster_name,
                resource_pool=vsphere_details.Ensilo_vcsa30.cluster_resources_pool
            )
            return self.vsphere_obj
        elif cluster_name:
            self.vsphere_obj = vsphere_operations.VsphereMachine(
                username=self.username,
                password=self.password,
                vm_name=self.vm_name,
                datastore_name=cluster_name.cluster_datastore_name,
                datacenter_name=cluster_name.cluster_name,
                resource_pool=cluster_name.cluster_resources_pool,
                vshost=cluster_name.cluster_vhost
            )
            return self.vsphere_obj
        else:
            return False


if __name__ == '__main__':
    vm = VsphereConnection().virtual_machine(vsphere_details.Ensilo_vcsa20)
    
    vm.search_vm_by_name("dima_colletor10x64")
    test = vm.vsphere_tests()
    snapshot_one = vm.snapshot_create(snapshot_name="test1")
    snapshot_two = vm.snapshot_create(snapshot_name="test2")

    vm.snapshot_revert_by_name("test1")

    vm.search_vm_by_name("dima_colletor10x64")