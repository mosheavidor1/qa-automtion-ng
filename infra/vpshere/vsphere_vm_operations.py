"""
This file is part of the operations in the Vsphere cluster on a VM.

References
----------
    - https://github.com/vmware/pyvmomi-community-samples - Community samples
    - https://github.com/vmware/pyvmomi/ - pyVmomi is the Python SDK for the vSphere
"""
import time

import allure
from pyVim.task import WaitForTask
from infra.allure_report_handler.reporter import Reporter

__author__ = "Dmitry Banny"


class VsphereMachineOperations:

    def __init__(self,
                 service_instance,
                 vm_obj):
        self._service_instance = service_instance
        self._vm_obj = vm_obj
        self._vm_data_parsed = {}
        self._snapshots_list = []
        self._snapshots_dict = {}

    @property
    def vm_data_parsed_dict(self) -> dict:
        return self._vm_data_parsed

    @property
    def snapshot_list(self) -> list:
        return self._snapshots_list

    @property
    def snapshots_dict(self) -> dict:
        return self._snapshots_dict

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
            raise Exception("No VM parsed data created")

    @allure.step("Create VM snapshot")
    def snapshot_create(self, snapshot_name, snapshot_description="", memory=True, quiesce=False):
        if self._vm_obj:
            task = self._vm_obj.CreateSnapshot_Task(name=snapshot_name,
                                                    description=snapshot_description,
                                                    memory=memory,
                                                    quiesce=quiesce)
            WaitForTask(task, self._service_instance)
            Reporter.report(f"Snapshot creation status: {task.info.state}")

            self._snapshots_list.append([snapshot_name, self._vm_obj.snapshot.currentSnapshot])
            current_snapshot = str(self._vm_obj.snapshot.currentSnapshot)
            Reporter.report(f"Snapshot name added: {snapshot_name} ({current_snapshot})")

            return current_snapshot
        else:
            raise Exception("No VM object created")

    @allure.step("Revert to snapshot with the name: {snapshot_name}")
    def snapshot_revert_by_name(self,
                                snapshot_name: str,
                                suppress_power_on: bool = False):
        """Revert to snapshot by name of the snapshot.

        Parameters
        ----------
        snapshot_name : object
            The name of the snapshot from a list of created / found snapshot names
        suppress_power_on : bool
            If suppressPowerOn is set to true,
            the virtual machine will not be powered on regardless of the power state when the current snapshot was created.
            defaults False
        """
        for item in self._snapshots_list:
            if item[0] == snapshot_name:
                Reporter.report(f"Snapshot found and starting revert to snapshot name: {snapshot_name}")
                try:
                    task = item[1].RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
                    WaitForTask(task, self._service_instance)

                    # Reporter.report(task)
                except Exception as e:
                    Reporter.report(str(e))

    @allure.step("Revert to VM snapshot creation order")
    def snapshot_revert_by_creation_order(self, number: int, suppress_power_on: bool = False):
        """This function reverts to a snapshot by a number.
        The order made by snapshots creation order.
        Parameters
        ----------
        number : int
            The number of the snapshot from a list
        suppress_power_on : bool
            If suppressPowerOn is set to true,
            the virtual machine will not be powered on regardless of the power state when the current snapshot was created.
            defaults False
        """
        if self._snapshots_list:
            revert_name, revert_object = self._snapshots_list[number]
            Reporter.report(f"Snapshot found and starting revert to snapshot name: {revert_name}")
            try:
                task = revert_object.RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
                WaitForTask(task, self._service_instance)
                # Reporter.report(f"Snapshot revert status: {task.info.state}")
            except Exception as e:
                # Reporter.report(f"Snapshot revert status: {task.info.state}")
                Reporter.report(str(e))

    @allure.step("Remove current VM snapshot")
    def snapshot_remove(self, remove_children=False):
        """This function removes a current snapshot.

        Usage
        ----------
        remove_children: bool
            Use this when all the children of the snapshot should be removed.
        """
        try:
            task = self.vm_obj.snapshot.currentSnapshot.RemoveSnapshot_Task(remove_children)
            WaitForTask(task, self._service_instance)
            Reporter.report(f"Snapshot removal status: {task}")
            if self._vm_obj.snapshot.currentSnapshot.name in self._snapshots_list:
                self._snapshots_list.pop(self.vm_obj.snapshot.currentSnapshot)
                Reporter.report(f"Snapshot from a snapshots list")
                # Reporter.report(f"Snapshot removal status: {task.info.state}")
        except Exception as e:
            # Reporter.report(f"Snapshot removal status: {task.info.state}")
            Reporter.report(str(e))

    @allure.step("Rename current VM snapshot")
    def snapshot_rename(self, new_name: str):
        """This function renames a current snapshot.

        Parameters
        ----------
        new_name : str
            New name of a snapshot
        """
        task = self.vm_obj.snapshot.currentSnapshot.Rename(new_name)
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Snapshot rename status: {task}")

    @allure.step("Remove all snapshots")
    def remove_all_snapshots(self):
        Reporter.report(f"Total snapshots: {len(self._snapshots_list)}, to be removed")
        task = self._vm_obj.RemoveAllSnapshots()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"All Snapshots removal status: {task}")

        self._snapshots_list.clear()
        Reporter.report(f"All Snapshots removal status: {task}")
        Reporter.report(f"Snapshots list: {len(self._snapshots_list)}")

    @allure.step("Print all snapshots")
    def get_all_snapshots(self, snapshots=None):
        raise Exception("Not implemented yet.")
        # TODO: get_all_snapshots
        # Print all the snapshots names
        # Print all the snapshots IDs ('vim.vm.Snapshot:snapshot-40013')
        # for snapshot_object in self._snapshots_list:
        #     snapshot_name, snapshot_object = self._snapshots_list
        # raise Exception("Not implemented yet.")

    @allure.step("Get VM snapshot-id by name")
    def get_snapshot_by_name(self, snapshot_name=None):
        try:
            if snapshot_name in self._snapshots_list[0]:
                Reporter.report("Snapshot-id found")
                return self._snapshots_list[0][snapshot_name]
        except AttributeError as e:
            Reporter.report(f"No snapshot-id found")
            Reporter.report(str(e))

    @allure.step("VM power reboot")
    def reboot(self):
        task = self._vm_obj.RebootGuest()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine restart: {task.info.state}")

    @allure.step("VM power on")
    def power_on(self):
        task = self._vm_obj.PowerOnVM_Task()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine power on: {task.info.state}")

    @allure.step("VM power off")
    def power_off(self):
        task = self._vm_obj.PowerOffVM_Task()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine power off: {task.info.state}")

    @allure.step("VM suspend")
    def suspend(self):
        task = self._vm_obj.Suspend()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine suspend: {task.info.state}")
