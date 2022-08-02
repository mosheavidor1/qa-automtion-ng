from logging import DEBUG

import allure
import time
from typing import List

import sut_details
import third_party_details
from infra.os_stations.linux_station import LinuxStation, COLLECTOR_TEMP_PATH
from infra.enums import FortiEdrSystemState, LinuxDistroTypes
from infra.system_components.collector import CollectorAgent
from infra.utils.utils import StringUtils
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.collectors.collectors_agents_utils import (
    wait_until_collector_pid_disappears,
    wait_until_collector_pid_appears
)
from sut_details import management_registration_password

PREFIX_INSTALLER_FILE_NAME = "FortiEDRCollectorInstaller"
SERVICE_NAME = "FortiEDRCollector"
COLLECTOR_INSTALLER_FOLDER_PATH = f"{COLLECTOR_TEMP_PATH}/version_files"
LINUX_LOCAL_MALWARE_FOLDER_PATH = f"{COLLECTOR_TEMP_PATH}/malware_simulator"
COLLECTOR_INSTALLATION_FOLDER_PATH = f"/opt/{SERVICE_NAME}"
COLLECTOR_SCRIPTS_FOLDER_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/scripts"
COLLECTOR_CRASH_DUMPS_FOLDER_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/CrashDumps/Collector"
COLLECTOR_BOOTSTRAP_FILENAME = "CollectorBootstrap.jsn"

COLLECTOR_CONTROL_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/control.sh"
COLLECTOR_CONFIG_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/Config/Collector"
COLLECTOR_CONFIG_SCRIPT_PATH = f"{COLLECTOR_SCRIPTS_FOLDER_PATH}/fortiedrconfig.sh"
COLLECTOR_BIN_PATH = f"{COLLECTOR_INSTALLATION_FOLDER_PATH}/bin/{SERVICE_NAME}"
CRASH_FOLDERS_PATHS = ["/var/crash", COLLECTOR_CRASH_DUMPS_FOLDER_PATH]

REGISTRATION_PASS = management_registration_password
DEFAULT_AGGREGATOR_PORT = 8081

SUPPORTED_MALWARE_FOLDER_NAME = "listen"
LINUX_SHARED_MALWARE_FOLDER_PATH = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\malware_sample\linux'


class LinuxCollector(CollectorAgent):
    def __init__(self, host_ip: str, user_name: str, password: str):
        super().__init__(host_ip=host_ip)
        self._os_station = LinuxStation(host_ip=host_ip, user_name=user_name, password=password)
        self.distro_type = self.os_station.distro_type
        self._process_id = self.get_current_process_id()
        self.__qa_files_path = "/home/qa"

    @property
    def cached_process_id(self) -> int:
        """ Caching the current process id in order later validate if it changed """
        return self._process_id

    @property
    def os_station(self) -> LinuxStation:
        return self._os_station

    @allure.step("Get current collector process ID")
    def get_current_process_id(self):
        process_ids = self.os_station.get_service_process_ids(COLLECTOR_BIN_PATH)
        process_id = process_ids[0] if process_ids is not None else None  # Why process_ids[0] who told that this is the correct one
        Reporter.report(f"Current process ID is: {process_id}")
        return process_id

    def get_qa_files_path(self):
        return self.__qa_files_path

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

    def get_configuration_files_details(self) -> List[dict]:
        raise NotImplemented("should be implemented")

    def get_the_latest_config_file_details(self):
        raise NotImplemented("should be implemented")

    def wait_for_new_config_file(self, latest_config_file_details=None):
        """
        wait until a new latest configuration file details received (latest from {current_config_file_details})
        """
        raise NotImplemented("Should be implemented")

    @allure.step("{0} - Stop collector")
    def stop_collector(self, password=None):
        password = password or REGISTRATION_PASS

        try:
            cmd = f"{COLLECTOR_CONTROL_PATH} --stop {password}"
            result = self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        except:
            cmd = f"{COLLECTOR_CONTROL_PATH} --stop {sut_details.management_registration_password}"
            result = self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)

        assert "stop operation succeeded" in result.lower(), f"Wrong output when stopping collector got: {result}"
        wait_until_collector_pid_disappears(self)
        self.update_process_id()

    @allure.step("{0} - Start collector")
    def start_collector(self):
        cmd = f"{COLLECTOR_CONTROL_PATH} --start"
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        wait_until_collector_pid_appears(self)
        self.update_process_id()

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

    @allure.step("{0} - Get agent status via cli")
    def get_agent_status(self):
        cmd = f"{COLLECTOR_CONTROL_PATH} --status"
        response = self.os_station.execute_cmd(cmd=cmd)
        forti_edr_service_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Service:\s+(\w+)', group=1)
        forti_edr_driver_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Driver:\s+(\w+)', group=1)
        forti_edr_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Status:\s+(\w+)', group=1)
        system_state = FortiEdrSystemState.NOT_RUNNING
        if forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Running':
            system_state = FortiEdrSystemState.RUNNING
        elif forti_edr_service_status == 'Down' and forti_edr_driver_status == 'Down' and forti_edr_status == 'Stopped':
            system_state = FortiEdrSystemState.DOWN
        elif forti_edr_service_status == 'Up' and forti_edr_driver_status == 'NONE' and forti_edr_status == 'Disabled':
            system_state = FortiEdrSystemState.DISABLED
        return system_state

    @allure.step("Reboot linux Collector")
    def reboot(self):
        self.os_station.reboot()
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    @allure.step("Check if collector files exist")
    def is_collector_files_exist(self) -> bool:
        result = self.os_station.is_path_exist(COLLECTOR_INSTALLATION_FOLDER_PATH)

        if result is True:
            Reporter.report("Collector files exist, probably still installed")
        else:
            Reporter.report("Collector files does not exist, probably not installed anymore")

        return result

    @allure.step("{0} - Get the collector's installed package name")
    def get_package_name(self):
        """ The package name is different in each linux distro"""
        package_name = self.os_station.get_installed_package_name(SERVICE_NAME)
        return package_name

    @allure.step("{0} - Uninstall linux Collector")
    def uninstall_collector(self, registration_password=None, stop_collector=True):
        """ Must stop collector before uninstallation """
        package_to_uninstall = self._get_package_name_to_uninstall()
        if stop_collector:
            self.stop_collector(registration_password)
        cmd = f"{self.os_station.distro_data.commands.uninstall} {package_to_uninstall}"
        result = self.os_station.execute_cmd(cmd=cmd, asynchronous=False)
        wait_until_collector_pid_disappears(self)
        self.update_process_id()
        return result

    @allure.step("{0} - Install linux agent")
    def pure_install_collector(self, installer_path):
        install_cmd = f"{self.os_station.distro_data.commands.install} {installer_path}"
        result = self.os_station.execute_cmd(cmd=install_cmd, fail_on_err=False)
        assert "FortiEDR Collector installed successfully" in result, f"{self} failed to install"

    # def _generate_installer_file_name(self, version):
    #     installer_file_name = fr"FortiEDRCollectorInstaller_#OS_DISTRO#-{version}.x86_64.rpm"
    #
    #     match self.os_station.os_name:
    #
    #         case 'CentOS Linux 8 (Core)':
    #             return installer_file_name.replace("#OS_DISTRO#", "CentOS8")
    #
    #         case 'CentOS Linux 7 (Core)':
    #             return installer_file_name.replace("#OS_DISTRO#", "CentOS7")
    #
    #         case 'CentOS Linux 6 (Core)':
    #             return installer_file_name.replace("#OS_DISTRO#", "CentOS6")
    #
    #     assert False, f"Can not conduct installer file name for OS: {self.os_station.os_name}"
    #
    @allure.step("{0} - Install FortiEDR Collector")
    def install_collector(self,
                          version: str,
                          aggregator_ip: str,
                          aggregator_port: int = None,
                          registration_password: str = None,
                          organization: str = None):

        installer_path = self.prepare_version_installer_file(collector_version=version)

        self.pure_install_collector(installer_path=installer_path)
        self.configure_collector(aggregator_ip=aggregator_ip,
                                 aggregator_port=aggregator_port,
                                 registration_password=registration_password,
                                 organization=organization)

    @allure.step("{0} - Configure linux Collector")
    def configure_collector(self, aggregator_ip, aggregator_port=None, registration_password=None, organization=None):
        """ Can't read the stdout of the configuration cmd,
        need to trigger the configuration -> close ssh transporter -> wait few sec """
        wait_after_configuration = 10  # Arbitrary
        aggregator_port = aggregator_port or DEFAULT_AGGREGATOR_PORT
        registration_password = registration_password or REGISTRATION_PASS

        if organization is None:
            organization = ''
        else:
            organization = f'--organization {organization}'

        cmd = f"{COLLECTOR_CONFIG_SCRIPT_PATH} --aggregator {aggregator_ip}:{aggregator_port} --password {registration_password} {organization}"
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True, return_output=False, attach_output_to_report=False)
        time.sleep(wait_after_configuration)  # Wait few sec after triggering the configuration cmd
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    def copy_log_parser_to_machine(self):
        pass

    def get_logs_content(self, file_suffix='.blg', filter_regex=None):
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

    @allure.step("Prepare linux collector installer file")
    def prepare_version_installer_file(self, collector_version):
        """ If the collector installer file does not exist on local machine, we will copy it from the shared drive """
        distro_version = self.os_station.distro_data.version_name
        suffix_type = self.os_station.distro_data.packages_suffix
        installer_file_name = f'{PREFIX_INSTALLER_FILE_NAME}_{distro_version}-{collector_version}.{suffix_type}'
        installer_local_path = f"{COLLECTOR_INSTALLER_FOLDER_PATH}/{installer_file_name}"
        is_installer_exist_on_machine = self.os_station.is_path_exist(path=installer_local_path)
        if not is_installer_exist_on_machine:
            Reporter.report(f"'{installer_local_path}' does not exist, copy it from shared folder")
            shared_drive_path = fr'{third_party_details.SHARED_DRIVE_LINUX_VERSIONS_PATH}\{collector_version}'
            self.os_station.copy_files_from_shared_folder(
                target_path_in_local_machine=COLLECTOR_INSTALLER_FOLDER_PATH, shared_drive_path=shared_drive_path,
                shared_drive_user_name=third_party_details.USER_NAME,
                shared_drive_password=third_party_details.PASSWORD,
                files_to_copy=[installer_file_name])
            assert self.os_station.is_path_exist(path=installer_local_path), \
                f"Installer file '{installer_local_path}' was not copied"
        return installer_local_path

    def _get_package_name_to_uninstall(self):
        """ Each linux distribution has its own collector package name for uninstallation """
        if self.os_station.distro_type == LinuxDistroTypes.UBUNTU:
            package_name_to_uninstall = PREFIX_INSTALLER_FILE_NAME.lower()
        elif self.os_station.distro_type == LinuxDistroTypes.CENTOS:
            package_name_to_uninstall = f"{PREFIX_INSTALLER_FILE_NAME}_{self.os_station.distro_data.version_name}"
        else:
            raise Exception(f"{self.os_station.distro_type} is not supported yet")

        return package_name_to_uninstall

    @allure.step("{0} - Create event {malware_name}")
    def create_event(self, malware_name=SUPPORTED_MALWARE_FOLDER_NAME):
        """ If the malware simulator does not exist on local machine, we will copy it from the shared drive """
        malware_folder_name = malware_name
        assert malware_folder_name == SUPPORTED_MALWARE_FOLDER_NAME, \
            f"Malware '{malware_folder_name}' is not supported in linux"
        local_malware_folder_path = f'{LINUX_LOCAL_MALWARE_FOLDER_PATH}/{malware_folder_name}'
        malware_file_path = f"{local_malware_folder_path}/test.sh"
        is_malware_file_exist_on_machine = self.os_station.is_path_exist(path=malware_file_path)
        if not is_malware_file_exist_on_machine:
            Reporter.report(f"'{malware_file_path}' does not exist, copy malware folder files from the shared drive")
            shared_malware_folder_path = fr'{LINUX_SHARED_MALWARE_FOLDER_PATH}\{malware_folder_name}'
            self.os_station.copy_files_from_shared_folder(
                target_path_in_local_machine=local_malware_folder_path, shared_drive_path=shared_malware_folder_path,
                shared_drive_user_name=third_party_details.USER_NAME,
                shared_drive_password=third_party_details.PASSWORD,
                files_to_copy=['*'])
            assert self.os_station.is_path_exist(path=malware_file_path), \
                f"Malware file '{malware_name}' was not copied"
        chmod_cmd = f"chmod +x {malware_file_path}"
        self.os_station.execute_cmd(cmd=chmod_cmd, fail_on_err=True, return_output=True,
                                    attach_output_to_report=True)
        self.os_station.execute_cmd(cmd="ps aux")
        pid = self.os_station.get_service_process_ids(malware_file_path)
        assert pid is None, f"{malware_name} already running pid is {pid}"
        trigger_event_cmd = f"cd {local_malware_folder_path}; {malware_file_path}"
        result = self.os_station.execute_cmd(cmd=trigger_event_cmd, fail_on_err=False, return_output=True,
                                             attach_output_to_report=True)
        self.os_station.execute_cmd(cmd="ps aux")
        return result

    def prepare_edr_event_tester_folder(self, network_path, filename):
        raise NotImplementedError()

    def create_bootstrap_backup(self, reg_password, filename=None):
        raise NotImplementedError()

    def restore_bootstrap_file(self, full_path_filename):
        raise NotImplementedError()

    def config_edr_simulation_tester(self, simulator_path, collector):
        raise NotImplementedError()

    @allure.step("Start EDR events tester")
    def start_edr_simulation_tester(self, simulator_path):
        raise NotImplementedError()

    @allure.step("EDR Event tester cleanup")
    def cleanup_edr_simulation_tester(self, edr_event_tester_path, filename):
        raise NotImplementedError()