import time
from datetime import datetime
from typing import List

import allure

import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.containers.system_component_containers import CollectorDetails
from infra.enums import SystemState, OsTypeEnum
from infra.system_components.collector import Collector
from infra.utils.utils import StringUtils


class WindowsCollector(Collector):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 collector_details: CollectorDetails,
                 encrypted_connection: bool = True):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password,
                         collector_details=collector_details,
                         os_type=OsTypeEnum.WINDOWS,
                         encrypted_connection=encrypted_connection)

        self.__collector_installation_path: str = r"C:\Program Files\Fortinet\FortiEDR"
        self.__collector_service_exe: str = f"{self.__collector_installation_path}\FortiEDRCollectorService.exe"
        self.__program_data: str = r"C:\ProgramData\FortiEdr"
        self.__counters_file: str = fr"{self.__program_data}\Logs\Driver\counters.txt"
        self.__crash_dumps_dir: str = fr"{self.program_data}\CrashDumps\Collector"
        self.__crash_dumps_info: str = fr"{self.__crash_dumps_dir}\crash_dumps_info.txt"
        self.__target_versions_path: str = "C:\\Versions"
        self.__target_helper_bat_files_path: str = "C:\\HelperBatFiles"
        self.__install_uninstall_logs_file_path: str = "C:\\InstallUninstallLogs"
        self.__memory_dmp_file_path: str = r'C:\WINDOWS\memory.dmp'
        self.__collected_crash_dump_dedicated_folder: str = r'C:\CrashDumpsCollected'
        self.__qa_files_path: str = "C:\\qa"

    @property
    def collector_installation_path(self) -> str:
        return self.__collector_installation_path

    @property
    def collector_service_ext(self) -> str:
        return self.__collector_service_exe

    @property
    def program_data(self) -> str:
        return self.__program_data

    @property
    def counters_file(self) -> str:
        return self.__counters_file

    @property
    def crash_dumps_dir(self) -> str:
        return self.__crash_dumps_dir

    def get_qa_files_path(self):
        return self.__qa_files_path

    def get_collector_info_from_os(self):
        pass

    def get_service_name(self) -> str:
        return "FortiEDRCollectorService."

    def _get_crash_folders(self) -> List[str]:
        """
        :return: the directories that crash files written to
        """
        return [r'C:\WINDOWS\system32\crashdumps', r'C:\WINDOWS\crashdumps', r'C:\WINDOWS\minidump',
                r'C:\WINDOWS\system32\config\systemprofile\AppData\Local\crashdumps']

    @allure.step("{0} - Get collector version")
    def get_version(self):
        cmd = f'"{self.__collector_service_exe}" -v'
        result = self.os_station.execute_cmd(cmd=cmd,
                                             return_output=True,
                                             fail_on_err=True,
                                             attach_output_to_report=True)
        version = StringUtils.get_txt_by_regex(text=result, regex='FortiEDR\s+Collector\s+Service\s+version\s+(\d+.\d+.\d+.\d+)', group=1)

        return version

    @allure.step("{0} - Stop collector")
    def stop_collector(self, password: str):
        cmd = f'"{self.__collector_service_exe}" --stop -rp:{password}'
        Reporter.report("Going to stop the collector")
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        self._process_id = None
        Reporter.report("Collector stopped successfully")

    @allure.step("{0} - Start collector")
    def start_collector(self):
        cmd = f'"{self.__collector_service_exe}" --start'
        Reporter.report("Going to start the collector")
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        self._update_process_id()
        Reporter.report("Collector started successfully")

    def is_up(self):
        pass

    def upgrade(self):
        pass

    def is_installed(self):
        pass

    def is_enabled(self):
        pass

    @allure.step("{0} - Copy collected crash dumps to C:\CrashDumpsCollected")
    def __move_crash_files_to_dedicated_crash_folder_files(self, dumps_files: List[str]):
        """
        The role of this method is to copy the dump files that collected during the test into specific folder
        :param dumps_files: list of the collected dump file to move
        """

        if dumps_files is not None and len(dumps_files) > 0:
            if not self.os_station.is_path_exist(self.__collected_crash_dump_dedicated_folder):
                self.os_station.create_new_folder(folder_path=self.__collected_crash_dump_dedicated_folder)
            for file in dumps_files:
                self.os_station.move_file(file_name=file, target_folder=self.__collected_crash_dump_dedicated_folder)

        else:
            Reporter.report("dumps files does not passed to this method - nothing to move")

    @allure.step("{0} - Checking if collector has crash")
    def has_crash(self) -> bool:
        curr_pid = self.get_current_process_id()
        is_pid_changed = False
        if curr_pid != self.process_id:
            is_pid_changed = True
            self._process_id = curr_pid
            Reporter.report(f"Process ID was changed, last known ID is: {self.process_id}, current ID is: {curr_pid}")

        has_dump = self.has_crash_dumps(append_to_report=False)

        if is_pid_changed or has_dump:
            Reporter.report("Crash was detected :(")
            return True

        Reporter.report("No crash detected :)")
        return False

    @allure.step("{0} - Checking if crash dumps exists")
    def has_crash_dumps(self, append_to_report: bool = False) -> bool:
        crash_dump_files = self.get_crash_dumps_files()

        found_crash_dumps = True if crash_dump_files is not None and len(crash_dump_files) else False
        if found_crash_dumps:
            Reporter.attach_str_as_file(file_name='crash_dumps', file_content=str('\r\n'.join(crash_dump_files)))
        else:
            Reporter.report(f"No crash dump file found in {self}")

        Reporter.report(f"Going to move crash dumps to {self.__collected_crash_dump_dedicated_folder}")
        self.__move_crash_files_to_dedicated_crash_folder_files(dumps_files=crash_dump_files)
        Reporter.report(f"!!!!!!! All the collected crash dumps moved to: {self.__collected_crash_dump_dedicated_folder} !!!!!!!")

        return found_crash_dumps

    @allure.step("Get crash dump files")
    def get_crash_dumps_files(self) -> List[str]:
        folder_to_search = self._get_crash_folders()

        crash_dumps_list = None
        for single_folder in folder_to_search:
            is_folder_exist = self.os_station.is_path_exist(single_folder)
            if is_folder_exist:
                files_in_folder = self.os_station.get_list_of_files_in_folder(folder_path=single_folder)
                if files_in_folder is not None and len(files_in_folder) > 0:
                    files_in_folder = [f'{single_folder}\{single_file}' for single_file in files_in_folder]

                    if crash_dumps_list is None:
                        crash_dumps_list = []

                    crash_dumps_list += files_in_folder

        is_memory_dump_exist = self.os_station.is_path_exist(path=self.__memory_dmp_file_path)
        if is_memory_dump_exist:
            if crash_dumps_list is None:
                crash_dumps_list = []

            crash_dumps_list += [self.__memory_dmp_file_path]

        return crash_dumps_list

    @allure.step("{0} - Get collector status")
    def get_collector_status(self) -> SystemState:
        cmd = f'"{self.__collector_service_exe}" --status'
        response = self.os_station.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False)

        forti_edr_service_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Service:\s+(\w+)', group=1)
        forti_edr_driver_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Driver:\s+(\w+)', group=1)
        forti_edr_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Status:\s+(\w+)', group=1)

        system_state = SystemState.NOT_RUNNING
        if forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Running':
            system_state = SystemState.RUNNING

        return system_state

    @allure.step("{0} - Validate collector is up and running")
    def validate_collector_is_up_and_running(self, use_health_monitor: bool=False):
        status = self.get_collector_status()
        if status == SystemState.RUNNING:
            Reporter.report("Collector is up and running :)")
        elif status == SystemState.NOT_RUNNING:
            Reporter.report("Collector is not up and running :(")
            if use_health_monitor:
                self.start_health_mechanism()
            else:
                assert False, "Collector is not up and running :("
        else:
            raise Exception(f"Unknown status: {status.name}")

    @allure.step('{0} - Start health mechanism')
    def start_health_mechanism(self):
        self.start_collector()
        state = self.get_collector_status()
        if state.RUNNING:
            Reporter.report("Health monitor successfully helped to bring collector service up")
        else:
            assert False, "Failed to start collector service, check what happens in logs"

    @allure.step("{0} - Install FortiEDR Collector")
    def install_collector(self,
                          version: str,
                          aggregator_ip: str,
                          organization: str = None,
                          aggregator_port: int = 8081,
                          registration_password: str = '12345678',
                          append_log_to_report=True):

        # create install-uninstall logs folder
        logs_folder = self.os_station.create_new_folder(folder_path=fr'{self.__install_uninstall_logs_file_path}')

        install_logs_file_name = f"install_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        install_log_file_name = fr"{logs_folder}\{install_logs_file_name}"

        shared_drive_path = rf'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'
        installation_files_folder = self.os_station.copy_files_from_shared_folder(
            target_path_in_local_machine=f'{self.__target_versions_path}\{version}',
            shared_drive_path=shared_drive_path, shared_drive_user_name=third_party_details.USER_NAME,
            shared_drive_password=third_party_details.PASSWORD, files_to_copy=['*'])

        list_of_file_in_folder = self.os_station.get_list_of_files_in_folder(folder_path=installation_files_folder, file_suffix=".msi")

        installer_file_name = fr"{installation_files_folder}\FortiEDRCollectorInstaller#archi#_{version}.msi"
        if '64-bit' in self.os_station.os_architecture:
            installer_file_name = installer_file_name.replace('#archi#', '64')
        elif '32-bit' in self.os_station.os_architecture:
            installer_file_name = installer_file_name.replace('#archi#', '32')
        else:
            raise Exception(f"Can not conduct installer file name since os station architecture is unknowns: {self.os_station.os_architecture}")

        if installer_file_name not in list_of_file_in_folder:
            assert False, f"Desired installer file: {installer_file_name} is not found in {installation_files_folder}"

        cmd = rf'msiexec /i "{installer_file_name}" /qn AGG={aggregator_ip}:{aggregator_port} PWD={registration_password} /LIME {install_log_file_name}'
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)

        self._process_id = self.get_current_process_id()
        if self._process_id is None:
            assert False, "Collector process id can not be None - Failing"

        if append_log_to_report:
            try:
                log_content = self.os_station.get_file_content(file_path=install_log_file_name)
                Reporter.attach_str_as_file(file_name=install_log_file_name, file_content=log_content)
            except Exception as e:
                Reporter.report("Faied to append log content into allure report")

    @allure.step("{0} - Uninstall FortiEDR Collector")
    def uninstall_collector(self, registration_password: str = '12345678', append_log_to_report=True):
        uninstall_script_file_name = 'uninstall_collector.bat'
        uninstall_logs_file_name = f"uninstall_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

        # create .bat file with the content above
        helper_bath_folder = self.os_station.create_new_folder(folder_path=fr'{self.__target_helper_bat_files_path}')

        # create install-uninstall logs folder
        logs_folder = self.os_station.create_new_folder(folder_path=fr'{self.__install_uninstall_logs_file_path}')

        uninstall_log_file_name = fr"{logs_folder}\{uninstall_logs_file_name}"

        script_content = f"""for /f %%a in (
'wmic product where "Name='Fortinet Endpoint Detection and Response Platform'" get IdentifyingNumber^^^|findstr "{{"'
) do set "val=%%a"
msiexec.exe /x %val% /qn UPWD="{registration_password}" RMCONFIG=1 /l*vx {uninstall_log_file_name}
"""

        uninstall_script_full_path = fr'{helper_bath_folder}\{uninstall_script_file_name}'
        is_uninstall_script_exist = self.os_station.is_path_exist(path=uninstall_script_full_path)
        if is_uninstall_script_exist:
            self.os_station.remove_file(file_path=uninstall_script_full_path)

        self.os_station.overwrite_file_content(content=script_content, file_path=uninstall_script_full_path)

        # execute the script
        self.os_station.execute_cmd(cmd=uninstall_script_full_path, asynchronous=True)

        self.wait_until_no_forti_service_exist(timeout=5*60)

        # update process id to None
        self._process_id = None

        self.wait_until_installation_folder_will_be_empty(timeout=2*60)

        if append_log_to_report:
            log_content = self.os_station.get_file_content(file_path=uninstall_log_file_name)
            Reporter.attach_str_as_file(file_name=uninstall_log_file_name, file_content=log_content)

    @allure.step("Wait until fortiEDR service won't be exist in tasklist")
    def wait_until_no_forti_service_exist(self, timeout=300):
        no_forti_service = False
        start_time = time.time()
        while not no_forti_service and time.time() - start_time < timeout:
            pid = self.get_current_process_id()
            if pid is None:
                no_forti_service = True
            else:
                time.sleep(10)

        if not no_forti_service:
            assert False, f"Uninstalled didn't complete within {timeout} seconds"

    @allure.step("Wait until installation folder will be empty")
    def wait_until_installation_folder_will_be_empty(self, timeout: int = 180):
        is_installation_folder_empty = False
        start_time = time.time()
        while not is_installation_folder_empty and time.time() - start_time < timeout:
            list_of_files_installation_folder = self.os_station.get_list_of_files_in_folder(
                folder_path=self.__collector_installation_path)

            if list_of_files_installation_folder is None or len(list_of_files_installation_folder) == 0:
                is_installation_folder_empty = True

            else:
                time.sleep(10)

        if not is_installation_folder_empty:
            # assert False, "Installation folder still contains files, should be empty"
            print("Installation folder still contains files, should be empty")

    def create_event(self, malware_name="DynamicCodeTests.exe"):
        malware_folder = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\malware_sample'
        target_folder = self.os_station.copy_files_from_shared_folder(self.get_qa_files_path(),
                                                                                malware_folder, [malware_name])

        self.os_station.execute_cmd(f'{target_folder}\\{malware_name}', asynchronous=True)