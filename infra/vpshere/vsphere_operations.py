"""
This file is part of the operations in the Vsphere cluster on a VM.

References
----------
    - https://github.com/vmware/pyvmomi-community-samples - Community samples
    - https://github.com/vmware/pyvmomi/ - pyVmomi is the Python SDK for the vSphere
"""

import atexit
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVim.task import WaitForTask

__author__ = "Dmitry Banny"

class VsphereMachine:
    def __init__(self, 
                 resource_pool: str,
                 datastore_name: str, 
                 datacenter_name: str, 
                 username: str,
                 password: str,
                 vshost: str=None,
                 vm_name: str=None,
                 template_name: str=None):
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
            [description], by default 'third_party_details.USER_NAME'
        password : str, optional
            [description], by default 'third_party_details.PASSWORD'
        vshost : str, optional
            [description], by default '10.51.100.120'
        """
        self.vm_data_parsed = None
        self._template_name: str = template_name
        self._vm_name: str = vm_name
        self._username: str = username
        self._password: str = password
        self._snapshots_list: list = []
        self._vm_obj = None
        self._snap_obj = None
        self._vm_ip_address = None
        self._resource_pool = resource_pool[0]  # Decide how to split the pools
        self._datastore_name = datastore_name
        self._datacenter_name = datacenter_name
        self._vshost = vshost
        try:
            self._service_instance = self.connect_to_vsphere()
        except Exception as e:
            print(f"Something went wrong while trying to connect to the vSphere {self._vshost}.\n{e.msg}")
        try:
            if self._vm_name:
                self.search_vm_by_name(self._vm_name)
            elif self._vm_ip_address:
                self.search_vm_by_ip(self._vm_ip_address)
            self.vm_info_parsed()
        except Exception as e:
            print(f"Something went wrong while trying to parse the vm_info {e}")


    def search_vm_by_name(self, vm_name):
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
        if self._service_instance:
            for vm_obj in self._service_instance.content.rootFolder.childEntity[0].vmFolder.childEntity:
                if vm_name == vm_obj.name:
                    print(f"VM found by name: {vm_name}")
                    self._vm_obj = vm_obj
            return self._vm_obj
        else:
            raise "No instance was created."

    def search_vm_by_ip(self, ip_address):
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
        for vm_obj in self._service_instance.content.rootFolder.childEntity[0].vmFolder.childEntity:
            try:
                print(vm_obj.guest.ipAddress)
                if ip_address == vm_obj.guest.ipAddress and vm_obj.guest.ipAddress and vm_obj.configStatus == 'green':
                    self._vm_obj = vm_obj
            except Exception as e:
                print(e)
        return self._vm_obj

    def connect_to_vsphere(self):
        try:
            self._service_instance = SmartConnectNoSSL(
                host=self._vshost,
                user=self._username,
                pwd=self._password
            )
            atexit.register(Disconnect, self._service_instance)
            return self._service_instance
        except IOError as io_error:
            print(io_error)
            return False

    def vm_info_parsed(self):
        """
        Print information for a particular virtual machine or recurse into a folder
        with depth protection

         Returns
        -------
        dict
            Returns an object that contains a VM information
        """
        if self._vm_obj:
            self.vm_data_parsed = {
                'vm_name': self._vm_obj.name,
                'vm_state': '',
                'snapshot': '',
                'guest_heartbeat': self._vm_obj.guestHeartbeatStatus,
                'guest_family': self._vm_obj.guest.guestFamily,
                'guest_full_name': self._vm_obj.guest.guestFullName,
                'guest_ip_address': self._vm_obj.guest.ipAddress,
                'guest_hotsname': self._vm_obj.guest.hostName,
                'guest_state': self._vm_obj.guest.guestState,
                'guest_status': self._vm_obj.guest.toolsStatus,
                'guest_uuid': self._vm_obj.datastore[0].info.vmfs.uuid
            }
            return self.vm_data_parsed
        else:
            raise Exception("No VM object created")

    def reset_vm(self, vm_name: str=None):
        # raise Exception("Not implemented yet.")
        try:
            WaitForTask(self._vm_obj.VmResettingEvent(), self._service_instance)
            print(f"Task: Successfully restarted vm: {vm_name}")
            return True
        except Exception as e:
            print(e)
            return False

    def snapshot_create(self, snapshot_name, snapshot_description="", memory=False, quiesce=False):
        if self._vm_obj:
            task = self._vm_obj.CreateSnapshot_Task(name=snapshot_name,
                                                    description=snapshot_description,
                                                    memory=memory,
                                                    quiesce=quiesce)
            WaitForTask(task, self._service_instance)
            print(f"Snapshot creation status: {task.info.state}")

            self._snapshots_list.append([snapshot_name, self._vm_obj.snapshot.currentSnapshot])
            print(f"Snapshot name added: {snapshot_name} ({self._vm_obj.snapshot.currentSnapshot})")

            return self._vm_obj.snapshot.currentSnapshot
        else:
            raise Exception("No VM object created")

    def snapshot_revert_by_name(self, snapshot_name: str):
        """Revert to snapshot by name of the snapshot.

        Parameters
        ----------
        snapshot_name : object
            The name of the snapshot from a list of created / found snapshot names
        """
        for item in self._snapshots_list:
            if item[0] == snapshot_name:
                print(f"Snapshot found and starting revert to snapshot name: {snapshot_name}")
                try:
                    task = item.RevertToSnapshot_Task()
                    WaitForTask(task, self._service_instance)

                    print(task)
                except Exception as e:
                    print(e)

    def snapshot_revert_by_creation_order(self, number: int):
        """This function reverts to a snapshot by a number.
        The order made by snapshots creation order.

        Parameters
        ----------
        number : int
            The number of the snapshot from a list

        """
        if self._snapshots_list:
            revert_name, revert_object = self._snapshots_list[number]
            print(f"Snapshot found and starting revert to snapshot name: {revert_name}")
            try:
                task = revert_object.RevertToSnapshot_Task()
                WaitForTask(task, self._service_instance)
                print(f"Snapshot revert status: {task.info.state}")
            except IndexError as e:
                print(e)
                raise "Revert to snapshot by creation order has failed"

    def vsphere_tests(self):
        result = self._vm_obj.VirtualMachineSnapshotInfo()

        return result

    def snapshot_remove(self, snapshot_object: object):
        raise Exception("Not implemented yet.")

        # task = snapshot_object.RemoveSnapshot_Task()
        # WaitForTask(task, self.service_instance)
        # try:
        #     self.snapshots_dict.pop(snapshot_object)
        # except Exception as e:
        #     print(e)
        # print(f"Snapshot removal status: {task}")

    def snapshot_rename(self, snapshot_object: object, new_name: str):
        raise Exception("Not implemented yet.")

    def get_all_snapshots(self, snapshots=None):
        raise Exception("Not implemented yet.")

        # snapshots_list = []
        # try:
        #     for snapshot in self.vm_obj.snapshot.rootSnapshotList:
        #         snapshot_dict = dict()
        #         snapshot_dict["snap_name"] = snapshot.name
        #         snapshot_dict["snap_obj"] = snapshot.snapshot
        #         snapshots_list.append(snapshot_dict)
        #         snapshots_list.append(self.snapshots_list + self.get_all_snapshots(snapshot.childSnapshotList))
        #     print(f"{self.snapshots_list}")
        #     return self.snapshots_list
        # except Exception as e:
        #     print(e)

    def get_snapshot_by_name(self, snapshot_name=None):
        # raise Exception("Not implemented yet.")
        try:
            if snapshot_name in self._snapshots_list:
                print("Snapshot found")
                return self._snapshots_list[snapshot_name]
        except AttributeError as e:
            print(f"There are no snapshots")
            return False

    def reboot(self):
        task = self._vm_obj.RebootGuest()
        WaitForTask(task, self._service_instance)
        raise Exception("Not implemented yet.")

        # print(f"Machine restart: {task.info.state}")
        # pass

    def task_status(self, task_id):
        raise Exception("Not implemented yet.")

    def power_on(self):
        task = self._vm_obj.PowerOnVM_Task()
        WaitForTask(task, self._service_instance)


    def power_off(self):

        task = self._vm_obj.PowerOffVM_Task()
        WaitForTask(task, self._service_instance)

    def start(self):
        raise Exception("Not implemented yet.")

        # print(f"Machine state change to power off: {task.info.state}")

