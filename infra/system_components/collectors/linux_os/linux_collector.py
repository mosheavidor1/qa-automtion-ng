import allure
import time
from infra.containers.system_component_containers import CollectorDetails
from infra.enums import OsTypeEnum, SystemState
from infra.system_components.collector import Collector
from infra.utils.utils import StringUtils
from infra.allure_report_handler.reporter import Reporter

SERVICE_NAME = "FortiEDRCollector"
COLLECTOR_INSTALLATION_FOLDER_PATH = F"/opt/{SERVICE_NAME}"
COLLECTOR_CONTROL_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/control.sh"
COLLECTOR_BIN_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/bin/{SERVICE_NAME}"


class LinuxCollector(Collector):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 collector_details: CollectorDetails):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password,
                         collector_details=collector_details,
                         os_type=OsTypeEnum.LINUX)

        self._process_id = self.get_current_process_id()

    @property
    def cached_process_id(self) -> int:
        """ Caching the current process id in order later validate if it changed """
        return self._process_id

    @allure.step("Get current collector process ID")
    def get_current_process_id(self):
        process_ids = self.os_station.get_service_process_ids(COLLECTOR_BIN_PATH)
        process_id = process_ids[0] if process_ids is not None else None  # Why process_ids[0] who told that this is the correct one
        Reporter.report(f"Current process ID is: {process_id}")
        return process_id

    @allure.step("Update process ID")
    def update_process_id(self):
        Reporter.report(f"Cached process ID is: {self._process_id}")
        self._process_id = self.get_current_process_id()
        Reporter.report(f"Collector process ID updated to: {self._process_id}")

    def get_version(self):
        pass

    def get_collector_info_from_os(self):
        pass

    def get_os_architecture(self):
        pass

    def stop_collector(self, password: str):
        pass

    def start_collector(self):
        pass

    def is_up(self):
        pass

    def upgrade(self):
        pass

    def is_installed(self):
        pass

    def is_enabled(self):
        pass

    @allure.step("{0} - Checking if collector has crash")
    def has_crash(self):
        curr_pid = self.get_current_process_id()
        cached_pid = self.cached_process_id
        has_crashed = False
        if curr_pid != cached_pid:
            has_crashed = True
            Reporter.report(f"{self} crashed because pid changed (from {cached_pid} to {curr_pid})")

        if self.has_crash_dumps(append_to_report=False):
            has_crashed = True
            Reporter.report(f"{self} crashed because found crash dumps, see report")

        if has_crashed:
            # create snapshot only if collector machine found on vSphere
            if self.os_station.vm_operations is not None:
                snapshot_name = f"snpashot_wit_crash_{time.time()}"
                self.os_station.vm_operations.snapshot_create(snapshot_name=snapshot_name)
                Reporter.report(f"Created New snapshot with the name: {snapshot_name}")

        Reporter.report(f"Is {self} crashed: {has_crashed} ")
        return has_crashed

    def has_crash_dumps(self, append_to_report: bool):
        pass

    @allure.step("{0} - Get collector status via cli")
    def get_collector_status(self):
        cmd = f"{COLLECTOR_CONTROL_PATH} --status"
        response = self.os_station.execute_cmd(cmd=cmd)
        forti_edr_service_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Service:\s+(\w+)', group=1)
        forti_edr_driver_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Driver:\s+(\w+)', group=1)
        forti_edr_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Status:\s+(\w+)', group=1)
        system_state = SystemState.NOT_RUNNING
        if forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Running':
            system_state = SystemState.RUNNING

        return system_state

    def is_status_running_in_cli(self):
        return self.get_collector_status() == SystemState.RUNNING

    def start_health_mechanism(self):
        pass

    def reboot(self):
        pass

    def install_collector(self, version: str, aggregator_ip: str, organization: str = None, aggregator_port: int = 8081,
                          registration_password: str = '12345678', append_log_to_report=True):
        pass

    def uninstall_collector(self, registration_password: str = '12345678', append_log_to_report=True):
        pass

    def copy_log_parser_to_machine(self):
        pass

    def append_logs_to_report(self, first_log_timestamp_to_append: str = None, file_suffix='.blg'):
        pass

    def clear_logs(self):
        pass

    def remove_all_crash_dumps_files(self):
        pass