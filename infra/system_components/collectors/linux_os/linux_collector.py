import allure
import time
from typing import List
import third_party_details
from infra.containers.system_component_containers import CollectorDetails
from infra.enums import OsTypeEnum, SystemState
from infra.system_components.collector import Collector
from infra.utils.utils import StringUtils
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.collectors.collectors_common_utils import (
    wait_until_collector_pid_disappears,
    wait_until_collector_pid_appears
)
from sut_details import management_registration_password

SERVICE_NAME = "FortiEDRCollector"
COLLECTOR_INSTALLER_FOLDER_PATH = "/tmp/version_files"
COLLECTOR_INSTALLATION_FOLDER_PATH = f"/opt/{SERVICE_NAME}"
COLLECTOR_SCRIPTS_FOLDER_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/scripts"
COLLECTOR_CRASH_DUMPS_FOLDER_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/CrashDumps/Collector"

COLLECTOR_CONTROL_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/control.sh"
COLLECTOR_CONFIG_PATH = f"{COLLECTOR_SCRIPTS_FOLDER_PATH}/fortiedrconfig.sh"
COLLECTOR_BIN_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/bin/{SERVICE_NAME}"
CRASH_FOLDERS_PATHS = ["/var/crash", COLLECTOR_CRASH_DUMPS_FOLDER_PATH]

REGISTRATION_PASS = management_registration_password
DEFAULT_AGGREGATOR_PORT = 8081


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

    @allure.step("{0} - Get collector version")
    def get_version(self):
        cmd = f"{COLLECTOR_CONTROL_PATH} --version"
        result = self.os_station.execute_cmd(cmd=cmd,
                                             return_output=True,
                                             fail_on_err=True,
                                             attach_output_to_report=True)
        version = StringUtils.get_txt_by_regex(text=result, regex='FortiEDR\s+Collector\s+version\s+(\d+.\d+.\d+.\d+)', group=1)

        return version

    def get_collector_info_from_os(self):
        pass

    @allure.step("{0} - Stop collector")
    def stop_collector(self, password=None):
        password = password or REGISTRATION_PASS
        cmd = f"{COLLECTOR_CONTROL_PATH} --stop {password}"
        result = self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        assert result.lower() == "stop operation succeeded"
        wait_until_collector_pid_disappears(self)
        self.update_process_id()

    @allure.step("{0} - Start collector")
    def start_collector(self):
        cmd = f"{COLLECTOR_CONTROL_PATH} --start"
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        wait_until_collector_pid_appears(self)
        self.update_process_id()

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

    @allure.step("{0} - Checking if crash dumps exists")
    def has_crash_dumps(self, append_to_report: bool = False) -> bool:
        """ The path of the crash dumps files will be attached to the report """
        crash_dump_files_path = self.get_crash_dumps_files_paths()
        if crash_dump_files_path is not None:
            Reporter.attach_str_as_file(file_name='crash_dumps', file_content=str('\r\n'.join(crash_dump_files_path)))
            return True
        else:
            Reporter.report(f"No crash dump file found in {self}")
            return False

    @allure.step("Get crash dump files paths")
    def get_crash_dumps_files_paths(self) -> List[str]:
        crash_dumps_paths = []
        for folder_path in CRASH_FOLDERS_PATHS:
            files_paths = self.os_station.get_list_of_files_in_folder(folder_path=folder_path)
            if files_paths is not None and len(files_paths) > 0:
                crash_dumps_paths += files_paths

        return crash_dumps_paths if len(crash_dumps_paths) > 0 else None

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
        elif forti_edr_service_status == 'Down' and forti_edr_driver_status == 'Down' and forti_edr_status == 'Stopped':
            system_state = SystemState.DOWN
        return system_state

    def is_status_running_in_cli(self):
        return self.get_collector_status() == SystemState.RUNNING

    def is_status_down_in_cli(self):
        return self.get_collector_status() == SystemState.DOWN

    def start_health_mechanism(self):
        pass

    @allure.step("Reboot linux Collector")
    def reboot(self):
        self.os_station.reboot()
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    @allure.step("Check if installation folder exists")
    def is_installation_folder_exists(self):
        result = self.os_station.is_path_exist(COLLECTOR_INSTALLATION_FOLDER_PATH)
        return result

    @allure.step("{0} - Get the installed package name")
    def get_installed_package_name(self):
        cmd = f"rpm -qa | grep -i {SERVICE_NAME}"
        full_name = self.os_station.execute_cmd(cmd=cmd, asynchronous=False)
        if full_name is None:
            return None
        short_name = full_name.split("-")[0]
        return short_name

    @allure.step("{0} - Uninstall linux Collector")
    def uninstall_collector(self, registration_password=None, stop_collector=True):
        """ Must stop collector before uninstallation """
        package_name = self.get_installed_package_name()
        assert package_name is not None, f"{self} is not installed"
        if stop_collector:
            self.stop_collector(registration_password)
        cmd = f"rpm -e {package_name}"
        result = self.os_station.execute_cmd(cmd=cmd, asynchronous=False)
        wait_until_collector_pid_disappears(self)
        self.update_process_id()
        return result

    @allure.step("{0} - Install linux Collector")
    def install_collector(self, installer_path):
        install_cmd = f"yum install -y {installer_path}"
        result = self.os_station.execute_cmd(cmd=install_cmd, fail_on_err=False)
        assert "FortiEDR Collector installed successfully" in result, f"{self} failed to install"

    @allure.step("{0} - Configure linux Collector")
    def configure_collector(self, aggregator_ip, aggregator_port=None, registration_password=None):
        """ Can't read the stdout of the configuration cmd,
        need to trigger the configuration -> close ssh transporter -> wait few sec """
        wait_after_configuration = 10  # Arbitrary
        aggregator_port = aggregator_port or DEFAULT_AGGREGATOR_PORT
        registration_password = registration_password or REGISTRATION_PASS
        cmd = f"{COLLECTOR_CONFIG_PATH} {aggregator_ip}:{aggregator_port} {registration_password}"
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True, return_output=False, attach_output_to_report=False)
        time.sleep(wait_after_configuration)  # Wait few sec after triggering the configuration cmd
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    def copy_log_parser_to_machine(self):
        pass

    def append_logs_to_report(self, first_log_timestamp_to_append: str = None, file_suffix='.blg'):
        pass

    def clear_logs(self):
        pass

    @allure.step("Remove crash dumps files")
    def remove_all_crash_dumps_files(self):
        files_paths = self.get_crash_dumps_files_paths()
        if files_paths is not None and isinstance(files_paths, list) and len(files_paths) > 0:
            Reporter.report(f"Remove crash files: {files_paths}")
            for file_path in files_paths:
                self.os_station.remove_file(file_path=file_path)

    @allure.step("Prepare linux collector version installer")
    def prepare_version_installer_file(self, version, package_name):
        """ If the collector installer file does not exist on local machine, we will copy it from the shared drive """
        arch = self.os_station.get_os_architecture()
        installer_name = f"{package_name}-{version}.{arch}.rpm"
        installer_local_path = f"{COLLECTOR_INSTALLER_FOLDER_PATH}/{installer_name}"
        is_installer_exist_on_machine = self.os_station.is_path_exist(path=installer_local_path)
        if not is_installer_exist_on_machine:
            Reporter.report(f"'{installer_local_path}' does not exist, copy it from shared folder")
            shared_drive_path = fr'{third_party_details.SHARED_DRIVE_LINUX_VERSIONS_PATH}\{version}'
            self.os_station.copy_files_from_shared_folder(
                target_path_in_local_machine=COLLECTOR_INSTALLER_FOLDER_PATH, shared_drive_path=shared_drive_path,
                shared_drive_user_name=third_party_details.USER_NAME,
                shared_drive_password=third_party_details.PASSWORD,
                files_to_copy=[installer_name])
            assert self.os_station.is_path_exist(path=installer_local_path), \
                f"Installer file '{installer_local_path}' was not copied"
        return installer_local_path
