"""This file is responsible for Rest API handle with the vSphere operations and getting information.
"""
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.enums import HttpRequestMethods
from infra.utils.utils import HttpRequesterUtils


class VsphereMachineRestApiOperations:
    def __init__(self, username: str, password: str, vhost: str, vm_name: str = None):
        self._auth = (username, password)
        self._vhost = vhost
        self._vm_name = vm_name
        self._vm_info = None
        self._vm_specifications = None

        self._headers = None
        self._session_id = None

        self.create_session_id()

    @property
    def vm_specifications(self):
        if self._vm_specifications:
            return self._vm_specifications
        else:
            Reporter.report(f"No specifications found.")
            return None

    @allure.step("Get a session ID")
    def create_session_id(self):
        """Creation of a session ID is must to run a commands via Rest-API."""
        path = "/rest/com/vmware/cis/session"

        response = HttpRequesterUtils.send_request(request_method=HttpRequestMethods.POST,
                                                   url=f"{self._vhost}{path}",
                                                   auth=self._auth)
        try:
            self._session_id = response['value']
            self._headers = {'vmware-api-session-id': self._session_id}

            Reporter.report(f"Session ID created. ({self._session_id})")
        except Exception as e:
            assert False, f"Session ID not created. ({e})"

    @allure.step("Get VM short information")
    def get_vm_specifications(self):
        """This function returns specifications of the machine setup in the vSphere."""
        self._get_vm_short_info_by_name()

        if self._vm_info:
            path = f"/rest/vcenter/vm/{self._vm_info['vm']}"
            response = HttpRequesterUtils.send_request(request_method=HttpRequestMethods.GET,
                                                       url=f"{self._vhost}{path}",
                                                       auth=self._auth,
                                                       headers=self._headers)
            return response

    def _get_vm_short_info_by_name(self):
        """This function finds a VM information by the name."""
        path = "/rest/vcenter/vm"

        all_vms = HttpRequesterUtils.send_request(request_method=HttpRequestMethods.GET,
                                                  url=f"{self._vhost}{path}",
                                                  auth=self._auth,
                                                  headers=self._headers)
        if all_vms:
            for vm_info in all_vms['value']:
                if vm_info['name'] == self._vm_name:
                    self._vm_info = vm_info
        else:
            assert False, f"All VMs list is empty. (len: {len(all_vms)})"

    @allure.step("Reboot VM")
    def vm_reboot(self):
        path = f"/rest/vcenter/vm/{self._vm_info['vm']}/power/reset"

        Reporter.report(f"Resetting VM: '{self._vm_info['vm']}'")
        HttpRequesterUtils.send_request(request_method=HttpRequestMethods.POST,
                                        url=f"{self._vhost}{path}",
                                        headers=self._headers,
                                        auth=self._auth)

    @allure.step("Power off VM")
    def vm_power_off(self):
        path = f"/rest/vcenter/vm/{self._vm_info['vm']}/power/stop"

        Reporter.report(f"Stopping VM: '{self._vm_info['vm']}'")
        HttpRequesterUtils.send_request(request_method=HttpRequestMethods.POST,
                                        url=f"{self._vhost}{path}",
                                        headers=self._headers,
                                        auth=self._auth)

    @allure.step("Suspend VM")
    def vm_suspend(self):
        path = f"/rest/vcenter/vm/{self._vm_info['vm']}/power/suspend"

        Reporter.report(f"Suspending VM: '{self._vm_info['vm']}'")
        HttpRequesterUtils.send_request(request_method=HttpRequestMethods.POST,
                                        url=f"{self._vhost}{path}",
                                        headers=self._headers,
                                        auth=self._auth)

    @allure.step("Start VM")
    def vm_start(self):
        path = f"/rest/vcenter/vm/{self._vm_info['vm']}/power/start"

        Reporter.report(f"Starting VM: '{self._vm_info['vm']}'")
        HttpRequesterUtils.send_request(request_method=HttpRequestMethods.POST,
                                        url=f"{self._vhost}{path}",
                                        headers=self._headers,
                                        auth=self._auth)


if __name__ == "__main__":
    vsphere = VsphereMachineRestApiOperations(username="ensilo\\automation",
                                              password="Aut0g00dqa42",
                                              vhost="https://10.51.100.120",
                                              vm_name="dima_colletor10x64")

    vm_information = vsphere.get_vm_specifications()
    vsphere.vm_reboot()
    vsphere.vm_suspend()
    vsphere.vm_power_off()
    vsphere.vm_start()
