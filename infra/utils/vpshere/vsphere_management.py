"""
References:
    - https://github.com/vmware/pyvmomi-community-samples - Community samples
    - https://github.com/vmware/pyvmomi/ - pyVmomi is the Python SDK for the vSphere
"""
import atexit
import vsphere_config
from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVim.task import WaitForTask


class VsphereMachine(object):

    def __init__(self,
                 vm_name: str = None,
                 template_name: str = None,
                 vm_ip_address: str = None,
                 resource_pool: str = "QA23",
                 datastore_name: str = "loc-vt23-r10-d1",
                 datacenter_name: str = "Ensilo_vcsa20",
                 username: str = r'ensilo\automation',
                 password: str = 'Aut0g00dqa42',
                 vshost: str = '10.51.100.120',
                 ):
        """The class build a VM object to operate the VM and provide all the needed data to perform various operations.

        Parameters
        ----------
        vm_name : str, optional (if template_name is provided)
            Represents a VM name in the known cluster, by default None
        template_name : str, optional (if vm_name is provided)
            [description], by default None
        vm_ip_address : str, optional
            [description], by default None
        resource_pool : str, optional
            [description], by default "QA23"
        datastore_name : str, optional
            [description], by default "loc-vt23-r10-d1"
        datacenter_name : str, optional
            [description], by default "Ensilo_vcsa20"
        username : str, optional
            [description], by default r'ensilo\automation'
        password : str, optional
            [description], by default 'Aut0g00dqa42'
        vshost : str, optional
            [description], by default '10.51.100.120'
        """        
        
        """
                The class constructor
                :param template_name: template (decided to remove it and use by IP address or VM name(?)
                :param vm_name: Name of the VM, defaults by None.
                :param resource_pool: Resource pool in the vsphere host, defaults by 'QA23'.
                :param datastore_name: the name of the datastore(storage) of the ESXi host.
                :param datacenter_name: the name of the datacenter inside the vSphere.
                :param username: vSphere login username.
                :param password: vSphere login password.
                :param vhost: vSphere IP address.

                Functions
                ----
                snapshot_create() - 
                revert_to_snapshot()
                delete_snapshot()

                suspend_vm()
                reset_vm()
                stop_vm()
                start_vm()
                destroy_vm()
                showdown_guest()
                standby_guest()
                reboot_guest()

                """
        self.template_name: str = template_name
        self.vm_name: str = vm_name
        self.username: str = username
        self.password: str = password
        self.snapshots_list: list = []
        self.vm_obj = None
        self.snap_obj = None
        self.vm_ip_address = vm_ip_address
        self.resource_pool = resource_pool[0]  # Decide how to split the pools
        self.datastore_name = datastore_name
        self.datacenter_name = datacenter_name
        self.vshost = vshost
        try:
            self.service_instance = self.connect_to_vsphere()
        except Exception as e:
            print(f"Something went wrong while trying to connect to the vSphere {self.vshost}. {e}")
        try:
            if self.vm_name:
                self.search_vm_by_name(self.vm_name)
            elif self.vm_ip_address:
                self.search_vm_by_ip(self.vm_ip_address)
            self.vm_info_parsed()
        except Exception as e:
            print(f"Something went wrong while trying to parse the vm_info {e}")

    def search_vm_by_name(self, vm_name):
        for vm_obj in self.service_instance.content.rootFolder.childEntity[0].vmFolder.childEntity:
            if vm_name == vm_obj.name:
                self.vm_obj = vm_obj
        return self.vm_obj

    def search_vm_by_ip(self, ip_address):
        for vm_obj in self.service_instance.content.rootFolder.childEntity[0].vmFolder.childEntity:
            if ip_address == vm_obj.guest.ipAddress:
                self.vm_obj = vm_obj
        return self.vm_obj

    def connect_to_vsphere(self):
        try:
            self.service_instance = SmartConnectNoSSL(
                host=self.vshost,
                user=self.username,
                pwd=self.password
            )
            atexit.register(Disconnect, self.service_instance)
            return self.service_instance
        except IOError as io_error:
            print(io_error)
            return False

    def vm_info_parsed(self):
        """
        Print information for a particular virtual machine or recurse into a folder
        with depth protection
        """
        self.vm_data_parsed = {
            'vm_name': self.vm_obj.name,
            'vm_state': '',
            'snapshot': '',
            # 'guest_heartbeat': self.vm_obj.guestHeartbeatStatus,
            'guest_family': self.vm_obj.guest.guestFamily,
            'guest_full_name': self.vm_obj.guest.guestFullName,
            'guest_ip_address': self.vm_obj.guest.ipAddress,
            'guest_hotsname': self.vm_obj.guest.hostName,
            'guest_state': self.vm_obj.guest.guestState,
            'guest_status': self.vm_obj.guest.toolsStatus,
            'guest_uuid': self.vm_obj.datastore[0].info.vmfs.uuid
        }
        return self.vm_data_parsed

    def reset_vm(self, vm_name=None):
        raise Exception("Not implemented yet.")
        try:
            WaitForTask(self.vm_obj.Reset())
            print(f"Task: Successfully restarted vm: {vm_name}")
            return True
        except Exception as e:
            print(e)
            return False

    def snapshot_create(self, snapshot_name, snapshot_description, memory=True, quiesce=False):
        task = WaitForTask(self.vm_obj.CreateSnapshot_Task(name=snapshot_name,
                                               description=snapshot_description,
                                               memory=memory,
                                               quiesce=quiesce))
        print(f"Snapshot creation status: {task}")

    def snapshot_revert(self, snapshot_name):
        raise Exception("Not implemented yet.")
        task = WaitForTask(self.vm_obj.snapshot.RevertToSnapshot_Task())

        print(task)
        raise Exception("Not implemented yet.")

    def snapshot_remove(self, snapshot_name):
        raise Exception("Not implemented yet.")        
        if snapshot_name:
            task = WaitForTask(self.vm_obj.snapshot.currentSnapshot.RemoveSnapshot_Task(
                name=snapshot_name
            ))
            self.snapshots_list.remove(snapshot_name)
            print(f"Snapshot removal status: {task}")
        

    def get_all_snapshots(self):
        raise Exception("Not implemented yet.")
        pass

    def reboot(self):
        raise Exception("Not implemented yet.")
        pass

    def task_status(self,task_id):
        raise Exception("Not implemented yet.")
        pass