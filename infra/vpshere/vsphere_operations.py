"""
This file is part of the operations in the Vsphere cluster on a VM.

References
----------
    - https://github.com/vmware/pyvmomi-community-samples - Community samples
    - https://github.com/vmware/pyvmomi/ - pyVmomi is the Python SDK for the vSphere
"""

from pyVim.task import WaitForTask

__author__ = "Dmitry Banny"

from infra.allure_report_handler.reporter import Reporter


class VsphereMachineOperations:

    def __init__(self,
                 service_instance,
                 vm_obj):
        self._service_instance = service_instance
        self._vm_obj = vm_obj
        self._vm_data_parsed = {}
        self._snapshots_list = []

    @property
    def vm_data_parsed_dict(self) -> dict:
        return self._vm_data_parsed

    @property
    def snapshot_list(self) -> []:
        return self._snapshots_list

    @property
    def vm_obj(self):
        return self._vm_obj

    def vm_info_parsed(self):
        """
        Reporter.report information for a particular virtual machine or recurse into a folder
        with depth protection

         Returns
        -------
        dict
            Returns an object that contains a VM information
        """
        if self._vm_obj:
            self._vm_data_parsed = {
                'vm_name': self._vm_obj.name,
                'vm_state': '',
                'snapshot': '',
                'guest_heartbeat': self._vm_obj.guestHeartbeatStatus,
                'guest_family': self._vm_obj.guest.guestFamily,
                'guest_full_name': self._vm_obj.guest.guestFullName,
                'guest_ip_address': self._vm_obj.guest.ipAddress,
                'guest_hostname': self._vm_obj.guest.hostName,
                'guest_state': self._vm_obj.guest.guestState,
                'guest_status': self._vm_obj.guest.toolsStatus,
                'guest_uuid': self._vm_obj.datastore[0].info.vmfs.uuid
            }
            return self._vm_data_parsed
        else:
            raise Exception("No VM object created")

    def reset_vm(self, vm_name: str=None):
        # raise Exception("Not implemented yet.")
        try:
            WaitForTask(self._vm_obj.VmResettingEvent(), self._service_instance)
            Reporter.report(f"Task: Successfully restarted vm: {vm_name}")
            return True
        except Exception as e:
            Reporter.report(str(e))
            return False

    def snapshot_create(self, snapshot_name, snapshot_description="", memory=False, quiesce=False):
        if self._vm_obj:
            task = self._vm_obj.CreateSnapshot_Task(name=snapshot_name,
                                                    description=snapshot_description,
                                                    memory=memory,
                                                    quiesce=quiesce)
            WaitForTask(task, self._service_instance)
            Reporter.report(f"Snapshot creation status: {task.info.state}")

            self._snapshots_list.append([snapshot_name, self._vm_obj.snapshot.currentSnapshot])
            Reporter.report(f"Snapshot name added: {snapshot_name} ({self._vm_obj.snapshot.currentSnapshot})")

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
                Reporter.report(f"Snapshot found and starting revert to snapshot name: {snapshot_name}")
                try:
                    task = item[1].RevertToSnapshot_Task()
                    WaitForTask(task, self._service_instance)

                    Reporter.report(task)
                except Exception as e:
                    Reporter.report(str(e))

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
            Reporter.report(f"Snapshot found and starting revert to snapshot name: {revert_name}")
            try:
                task = revert_object.RevertToSnapshot_Task()
                WaitForTask(task, self._service_instance)
                Reporter.report(f"Snapshot revert status: {task.info.state}")
            except IndexError as e:
                Reporter.report(str(e))
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
        #     Reporter.report(str(e))
        # Reporter.report(f"Snapshot removal status: {task}")

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
        #     Reporter.report(f"{self.snapshots_list}")
        #     return self.snapshots_list
        # except Exception as e:
        #     Reporter.report(str(e))

    def get_snapshot_by_name(self, snapshot_name=None):
        # raise Exception("Not implemented yet.")
        try:
            if snapshot_name in self._snapshots_list:
                Reporter.report("Snapshot found")
                return self._snapshots_list[snapshot_name]
        except AttributeError as e:
            Reporter.report(f"There are no snapshots")
            return False

    def reboot(self):
        task = self._vm_obj.RebootGuest()
        WaitForTask(task, self._service_instance)
        raise Exception("Not implemented yet.")

        # Reporter.report(f"Machine restart: {task.info.state}")
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

        # Reporter.report(f"Machine state change to power off: {task.info.state}")

