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
from pyVmomi import vim
from infra.allure_report_handler.reporter import Reporter

__author__ = "Dmitry Banny"

from infra.enums import OsPowerState


class VsphereMachineOperations:

    CLEAN_OS_SNAPSHOT_NAME = 'clean_os'

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
        all_snapshots = self.get_all_snapshots()
        if len(all_snapshots) > 4:
            assert False, f"There are already {len(all_snapshots)} snapshots, will not create " \
                          f"more snapshots till previous will be removed or investigated"

        if self.is_snapshot_name_exist(snapshot_name=snapshot_name):
            assert False, f"Can not create snapshot with the name: {snapshot_name} since it's already exist"

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

    def is_snapshot_name_exist(self, snapshot_name):
        all_snapshots_objs = self.get_all_snapshots()
        all_snapshot_names = [x.name for x in all_snapshots_objs]

        if snapshot_name in all_snapshot_names:
            return True

        return False

    @allure.step("Remove snapshot with the name: {snapshot_name}")
    def snapshot_remove_by_name(self, snapshot_name):
        if snapshot_name == self.CLEAN_OS_SNAPSHOT_NAME:
            assert False, f"Can not remove snapshot with the name: {self.CLEAN_OS_SNAPSHOT_NAME}"

        all_snapshots = self.get_all_snapshots()
        is_found = False
        for snapshot_tree in all_snapshots:
            if snapshot_tree.name == snapshot_name:
                is_found = True
                task = snapshot_tree.snapshot.RemoveSnapshot_Task(False)
                WaitForTask(task, self._service_instance)

        assert is_found, f"did not found any snapshot with the name: {snapshot_name}"

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
                task = item[1].RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
                WaitForTask(task, self._service_instance)
                return
        raise Exception(f"Snapshot '{snapshot_name}' was not found")

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
    def snapshot_remove_current(self, remove_children=False):
        """This function removes a current snapshot.

        Usage
        ----------
        remove_children: bool
            Use this when all the children of the snapshot should be removed.
        """
        try:
            if self.vm_obj.snapshot.currentSnapshot.name == self.CLEAN_OS_SNAPSHOT_NAME:
                assert False, f"Can not remove snapshot with the name: {self.CLEAN_OS_SNAPSHOT_NAME}"

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
    def rename_current_snapshot(self, new_name: str):
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
        all_snapshots = self.get_all_snapshots()
        for snapshot_tree in all_snapshots:
            if snapshot_tree.name != self.CLEAN_OS_SNAPSHOT_NAME:
                task = snapshot_tree.snapshot.RemoveSnapshot_Task(False)
                WaitForTask(task, self._service_instance)

    # @allure.step("Remove all snapshots")
    # def remove_all_snapshots(self):
    #     Reporter.report(f"Total snapshots: {len(self._snapshots_list)}, to be removed")
    #     task = self._vm_obj.RemoveAllSnapshots()
    #     WaitForTask(task, self._service_instance)
    #     # Reporter.report(f"All Snapshots removal status: {task}")
    #
    #     self._snapshots_list.clear()
    #     Reporter.report(f"All Snapshots removal status: {task}")
    #     Reporter.report(f"Snapshots list: {len(self._snapshots_list)}")

    @allure.step("Get all snapshot objects")
    def get_all_snapshots(self):
        results = []
        try:
            root_snapshots = self.vm_obj.snapshot.rootSnapshotList
        except:
            root_snapshots = []

        for snapshot in root_snapshots:
            results.append(snapshot)
            results += self._get_child_snapshots(snapshot)

        return results

    def _get_child_snapshots(self, snapshot):
        results = []
        snapshots = snapshot.childSnapshotList

        for snapshot in snapshots:
            results.append(snapshot)
            results += self._get_child_snapshots(snapshot)

        return results

    @allure.step("Revert to root snapshot")
    def revert_to_root_snapshot(self):
        task = self._vm_obj.snapshot.rootSnapshotList[0].snapshot.RevertToSnapshot_Task(suppressPowerOn=False)
        WaitForTask(task, self._service_instance)

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
        self._wait_for_desired_power_state(desired_state=OsPowerState.RUNNING)

    @allure.step("VM power off")
    def power_off(self):
        task = self._vm_obj.PowerOffVM_Task()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine power off: {task.info.state}")
        self._wait_for_desired_power_state(desired_state=OsPowerState.NOT_RUNNING)

    @allure.step("VM suspend")
    def suspend(self):
        task = self._vm_obj.Suspend()
        WaitForTask(task, self._service_instance)
        # Reporter.report(f"Machine suspend: {task.info.state}")

    @allure.step("Remove VM")
    def remove_vm(self):
        Reporter.report("Powering off the VM before removal")
        self.power_off()
        Reporter.report("Removing VM from VSphere inventory")
        task = self.vm_obj.Destroy_Task()
        WaitForTask(task, self._service_instance)

    @allure.step("Create VM from template")
    def clone_vm_by_name(self,
                         vm_template_object,
                         resource_pool_object,
                         folder_object,
                         new_vm_name,
                         power_on=True):

        Reporter.report("Cloning specifications of the template")
        spec_clone = self._create_clone_spec(
            resource_pool_object=resource_pool_object, power_on=power_on
        )

        Reporter.report("Start VM cloning and wait for task finished")
        task = vm_template_object.Clone(
            folder=folder_object, name=new_vm_name, spec=spec_clone
        )
        WaitForTask(task, self._service_instance)
        assert task.info.state == 'success', f"VM clone state: {task.info.state}"

        return task.info.result

    def is_power_on(self):
        if self._vm_obj.guest.guestState == 'running':
            return True

        return False

    def is_power_off(self):
        if self._vm_obj.guest.guestState == 'notRunning':
            return True

        return False

    @allure.step("Renamge VM in vSphere")
    def rename_machine_in_vsphere(self, new_name: str):
        task = self._vm_obj.Rename(new_name)
        WaitForTask(task, self._service_instance)

    def _create_clone_spec(self, resource_pool_object, power_on: bool=True):
        clone_spec = vim.vm.CloneSpec()

        relocatespec = vim.vm.RelocateSpec()
        relocatespec.pool = resource_pool_object
        clone_spec.location = relocatespec
        clone_spec.powerOn = power_on

        return clone_spec

    @allure.step("Wait until VM will be in power state: desired_state")
    def _wait_for_desired_power_state(self,
                                      desired_state: OsPowerState,
                                      timeout: int = 60):
        expected_string = None
        if desired_state == OsPowerState.RUNNING:
            expected_string = 'running'

        elif desired_state == OsPowerState.NOT_RUNNING:
            expected_string = 'notRunning'

        else:
            raise Exception(f'desired state: {desired_state} does not supported')

        start_time = time.time()
        is_in_desired_state = False
        while time.time() - start_time < timeout and not is_in_desired_state:
            if self._vm_obj.guest.guestState == expected_string:
                is_in_desired_state = True
            else:
                time.sleep(1)

        assert is_in_desired_state, f"VM is not in desired state within {timeout}"
