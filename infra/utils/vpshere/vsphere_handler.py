
import vsphere_config
import vsphere_management

__author__ = "Dmitry Banny"


class VsphereConnection(object):
    """ This class provides a connection to a Vsphere """

    def __init__(self, username="ensilo\\automation", password="Aut0g00dqa42", vm_name=None, malware=False):
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
        self._password = password
        self._username = username
        self._vm_name = vm_name
        self._malware = malware

    def cluster(self, cluster_name):
        """This function represents a VM object.

        Usage example
        ----------
        vm = VsphereConnection(vm_name="dima_colletor10x64").cluster(vsphere_config.Ensilo_vcsa20)
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
            vsphere_obj = vsphere_management.VsphereMachine(
                username=self._username,
                password=self._password,
                vm_name=self._vm_name,
                datastore_name=vsphere_config.Ensilo_vcsa30.datastore_name,
                datacenter_name=vsphere_config.Ensilo_vcsa30.name,
                resource_pool=vsphere_config.Ensilo_vcsa30.resource_pools
            )
            return vsphere_obj
        elif cluster_name:
            vsphere_obj = vsphere_management.VsphereMachine(
                username=self._username,
                password=self._password,
                vm_name=self._vm_name,
                datastore_name=cluster_name.datastore_name,
                datacenter_name=cluster_name.name,
                resource_pool=cluster_name.resource_pools
            )
            return vsphere_obj


if __name__ == '__main__':
    vm = VsphereConnection(vm_name="dima_colletor10x64").cluster(vsphere_config.Ensilo_vcsa20)
    # vm.get_all_snapshots()
    # vm.snapshot_create(snapshot_name="test 1", snapshot_description="test description")
    vm.snapshot_remove(snapshot_name="test 1")
    vm.reboot()


