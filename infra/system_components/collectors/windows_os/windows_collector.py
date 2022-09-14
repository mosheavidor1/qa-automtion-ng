import time
from datetime import datetime
from typing import List, Dict
import logging
import allure

import third_party_details
from infra.common_utils import wait_for_condition
from infra.os_stations.windows_station import WindowsStation
from infra.system_components.collectors.collectors_agents_utils import (
    wait_until_collector_pid_disappears,
    wait_until_collector_pid_appears
)
from infra.allure_report_handler.reporter import Reporter, INFO
from infra.system_components.collector import CollectorAgent, FILENAME_EDR_TESTER
from infra.enums import FortiEdrSystemState
from infra.system_components.collectors.default_values import MAX_WAIT_FOR_NEW_CONFIG_FILE_TO_APPEAR, \
    CONFIG_FILE_APPEAR_INTERVAL
from infra.utils.utils import StringUtils
from sut_details import default_organization_registration_password
from infra.system_components.collectors.windows_os.windows_collector_installation_utils import (
    create_uninstallation_script,
    get_installer_path,
    generate_installation_cmd
)

logger = logging.getLogger(__name__)

INTERVAL_WAIT_FOR_SERVICE = 5
MAX_WAIT_FOR_SERVICE = 60
REGISTRATION_PASS = default_organization_registration_password
DEFAULT_AGGREGATOR_PORT = 8081
SERVICE_NAME = "FortiEDRCollectorService."
INSTALL_UNINSTALL_LOGS_FOLDER_PATH = "C:\\InstallUninstallLogs"
EXTRACT_EDR_EVENT_TESTER_TIMEOUT = 30
EDR_EVENT_TESTER_TIMEOUT = 1200


class WindowsCollector(CollectorAgent):

    def __init__(self, host_ip: str, user_name: str, password: str):
        super().__init__(host_ip=host_ip)
        self._os_station = WindowsStation(host_ip=host_ip, user_name=user_name, password=password)
        self._process_id = self.get_current_process_id()
        self.__collector_installation_path: str = r"C:\Program Files\Fortinet\FortiEDR"
        self.__collector_service_exe: str = f"{self.__collector_installation_path}\FortiEDRCollectorService.exe"
        self.__program_data: str = r"C:\ProgramData\FortiEdr"
        self.__counters_file: str = fr"{self.__program_data}\Logs\Driver\counters.txt"
        self.__crash_dumps_dir: str = fr"{self.program_data}\CrashDumps\Collector"
        self.__target_logs_folder: str = "C:\\ParsedLogsFolder"
        self.__memory_dmp_file_path: str = r'C:\WINDOWS\memory.dmp'
        self.__collected_crash_dump_dedicated_folder: str = r'C:\CrashDumpsCollected'
        self.__collector_logs_folder: str = f"{self.__program_data}\Logs"
        self.__collector_config_folder: str = f"{self.__program_data}\Config\Collector"
        self.__collector_config_updates_folder: str = fr"{self.__collector_config_folder}\Updates"
        self.__bootstrap_file_name: str = "CollectorBootstrap.jsn"
        self.__qa_files_path: str = r"C:\qa"
        self._kill_all_undesired_processes()
        self._initial_version = self.get_version(safe=True)

    @property
    def os_station(self) -> WindowsStation:
        return self._os_station

    @property
    def initial_version(self) -> str:
        return self._initial_version

    @allure.step("Kill all undesired process that running on windows collector")
    def _kill_all_undesired_processes(self):
        # TODO - Remove this method when we will have new templates
        processes = ['nssm.exe', 'blg2log.exe', 'filebeat.exe']
        for single_process in processes:
            pids = self.os_station.get_service_process_ids(single_process)
            if pids is not None and len(pids) > 0:
                for pid in pids:
                    self.os_station.kill_process_by_id(pid=pid)

    @property
    def collector_installation_path(self) -> str:
        return self.__collector_installation_path

    @property
    def cached_process_id(self) -> int:
        """ Caching the current process id in order later validate if it changed """
        return self._process_id

    @property
    def collector_service_ext(self) -> str:
        return self.__collector_service_exe

    @property
    def program_data(self) -> str:
        return self.__program_data

    @property
    def collector_config_folder(self) -> str:
        return self.__collector_config_folder

    @property
    def counters_file(self) -> str:
        return self.__counters_file

    @allure.step("Get current collector process ID")
    def get_current_process_id(self):
        process_ids = self.os_station.get_service_process_ids(SERVICE_NAME)
        process_id = process_ids[0] if process_ids is not None else None  # Why process_ids[0] who told that this is the correct one
        Reporter.report(f"Current process ID is: {process_id}")
        return process_id

    def get_configuration_files_details(self) -> List[dict]:
        """
        return these data of the configuration files: names, sizes, datetime, sorted by timestamp.
        """
        folder_path = self.__collector_config_updates_folder
        config_files_details = self.os_station.get_files_details_in_folder(folder_path=folder_path,
                                                                           desired_files_suffix='.jsn',
                                                                           ignore_file_suffix='.jsn.failed',
                                                                           ordered_by_date_time=True)
        return config_files_details

    def get_the_latest_config_file_details(self) -> dict:
        """
        return these data of the latest created configuration file: names, sizes, datetime
        """
        config_files_details = self.get_configuration_files_details()  # sorted by timestamp
        return config_files_details[-1]

    @allure.step("Wait for a new configuration file")
    def wait_for_new_config_file(self, config_files_details_before_action: List[dict] = None):
        """
        Wait for a new configuration file received by datetime according to the resolution of minutes,
        If the size of the new config file is smaller than the size of the last config file then it is a bug in Infra
        because the list of config files received sorted by datetime.
        If the new config file was received in the same minute as the last config file, check that the new config
        file didn't exist in the list of recent config files to validate that it is a new file and not and not actually
        the last config, because then no new file was received.
        And if the size of the latest config file is larger than the size of the last file, then a new file has been received.
        """
        config_files_details_before_action = config_files_details_before_action or self.get_configuration_files_details()
        latest_config_file_details = config_files_details_before_action[-1]
        latest_config_file_datetime = latest_config_file_details['file_datetime']
        logger.info(f"the current latest file datetime is: {latest_config_file_datetime},wait for a new config")

        def condition():
            updated_latest_config_file_details = self.get_the_latest_config_file_details()
            updated_latest_config_file_datetime = updated_latest_config_file_details['file_datetime']
            logger.info(f"time of the updated latest config is {updated_latest_config_file_datetime}")
            if updated_latest_config_file_datetime < latest_config_file_datetime:
                raise Exception("Infra bug! The configuration files list are not sorted by creation datetime")
            elif updated_latest_config_file_datetime == latest_config_file_datetime:
                return not any(updated_latest_config_file_details['file_name'] == config_file['file_name'] and \
                               updated_latest_config_file_details['file_datetime'] == config_file['file_datetime']
                               for config_file in config_files_details_before_action)
            elif updated_latest_config_file_datetime > latest_config_file_datetime:
                return True

        logger.info(f"Wait until a new latest configuration file received,"
                    f" current latest is {latest_config_file_details}")

        wait_for_condition(condition_func=condition,
                           timeout_sec=MAX_WAIT_FOR_NEW_CONFIG_FILE_TO_APPEAR,
                           interval_sec=CONFIG_FILE_APPEAR_INTERVAL,
                           condition_msg=f"{self} got new configuration file")

    def get_qa_files_path(self):
        return self.__qa_files_path

    def _get_crash_folders(self) -> List[str]:
        """
        :return: the directories that crash files written to
        """
        return [r'C:\WINDOWS\system32\crashdumps',
                r'C:\WINDOWS\crashdumps',
                r'C:\WINDOWS\minidump',
                r'C:\WINDOWS\system32\config\systemprofile\AppData\Local\crashdumps',
                r'C:\ProgramData\FortiEDR\Dumps\Collector']

    @allure.step("{0} - Get collector version")
    def get_version(self, safe: bool = False):
        try:
            cmd = f'"{self.__collector_service_exe}" -v'
            result = self.os_station.execute_cmd(cmd=cmd,
                                                 return_output=True,
                                                 fail_on_err=True,
                                                 attach_output_to_report=True)
            version = StringUtils.get_txt_by_regex(text=result, regex='FortiEDR\s+Collector\s+Service\s+version\s+(\d+.\d+.\d+.\d+)', group=1)
        except Exception as e:
            if safe:
                return None
            else:
                raise e

        return version

    @allure.step("{0} - Stop collector")
    def stop_collector(self, password=None):
        logger.info(f"Stop {self}")
        password = password or REGISTRATION_PASS

        cmd = f'"{self.__collector_service_exe}" --stop -rp:{password}'
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True, asynchronous=False)

        wait_until_collector_pid_disappears(self)
        self.update_process_id()

    @allure.step("{0} - Start collector")
    def start_collector(self):
        logger.info(f"Start {self}")
        cmd = f'"{self.__collector_service_exe}" --start'
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    @allure.step("Update process ID")
    def update_process_id(self):
        Reporter.report(f"Cached process ID is: {self._process_id}", logger.debug)
        self._process_id = self.get_current_process_id()
        Reporter.report(f"Collector process ID updated to: {self._process_id}", logger.debug)

    @allure.step("Reboot Collector")
    def reboot(self):
        self.os_station.reboot()
        wait_until_collector_pid_appears(self)
        self.update_process_id()

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
        if curr_pid != self.cached_process_id:
            is_pid_changed = True
            Reporter.report(f"Process ID was changed, last known ID is: {self.cached_process_id}, current ID is: {curr_pid}")

        has_dump = self.has_crash_dumps(append_to_report=False)

        if is_pid_changed or has_dump:
            Reporter.report("Crash was detected :(")

            # create snapshot only if collector machine found on vSphere
            #if self.os_station.vm_operations is not None:
               # snapshot_name = f"snpashot_wit_crash_{time.time()}"
#                self.os_station.vm_operations.snapshot_create(snapshot_name=snapshot_name)
             #   Reporter.report(f"Created New snapshot with the name: {snapshot_name}")
            return True

        Reporter.report("No crash detected :)")
        return False

    @allure.step("{0} - Checking if crash dumps exists")
    def has_crash_dumps(self, append_to_report: bool = False) -> bool:
        crash_dump_files = self.get_crash_dumps_files()

        found_crash_dumps = True if crash_dump_files is not None and len(crash_dump_files) > 0 else False
        if found_crash_dumps:
            logger.info(f"Found crash dumps: {crash_dump_files}")
            Reporter.attach_str_as_file(file_name='crash_dumps', file_content=str('\r\n'.join(crash_dump_files)))
        else:
            Reporter.report(f"No crash dump file found in {self}", logger_func=logger.info)

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
                    files_in_folder = [fr'{single_folder}\{single_file}' for single_file in files_in_folder]
                    if 'C:\ProgramData\FortiEDR\Dumps\Collector\TMP' in files_in_folder:
                        files_in_folder.remove('C:\ProgramData\FortiEDR\Dumps\Collector\TMP')

                    if single_folder == 'C:\ProgramData\FortiEDR\Dumps\Collector':
                        files_in_folder = [file for file in files_in_folder if not file.endswith('.exe.mem')]

                    if crash_dumps_list is None:
                        crash_dumps_list = []

                    crash_dumps_list += files_in_folder

        is_memory_dump_exist = self.os_station.is_path_exist(path=self.__memory_dmp_file_path)
        if is_memory_dump_exist:
            if crash_dumps_list is None:
                crash_dumps_list = []

            crash_dumps_list += [self.__memory_dmp_file_path]

        return crash_dumps_list

    @allure.step("Remove crash dumps files")
    def remove_all_crash_dumps_files(self):
        paths = self.get_crash_dumps_files()
        if paths is not None and isinstance(paths, list) and len(paths) > 0:
            for path in paths:
                if self.os_station.is_folder(path=path):
                    Reporter.report(f"Removing folder: {path}", logger_func=logger.info)
                    self.os_station.remove_folder(folder_path=path)
                else:
                    Reporter.report(f"Removing file: {path}", logger_func=logger.info)
                    self.os_station.remove_file(file_path=path)

    @allure.step("{0} - Get collector status via cli")
    def get_agent_status(self) -> FortiEdrSystemState:
        cmd = f'"{self.__collector_service_exe}" --status'
        response = self.os_station.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False)

        forti_edr_service_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Service:\s+(\w+)', group=1)
        forti_edr_driver_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Driver:\s+(\w+)', group=1)
        forti_edr_status = StringUtils.get_txt_by_regex(text=response, regex='FortiEDR\s+Status:\s+(\w+)', group=1)

        system_state = FortiEdrSystemState.NOT_RUNNING
        if forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Running':
            system_state = FortiEdrSystemState.RUNNING
        elif forti_edr_service_status == 'Down' and forti_edr_driver_status is None and forti_edr_status is None:
            system_state = FortiEdrSystemState.DOWN
        elif forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Disabled':
            system_state = FortiEdrSystemState.DISABLED
        elif forti_edr_service_status == 'Up' and forti_edr_driver_status == 'Up' and forti_edr_status == 'Isolated':
            system_state = FortiEdrSystemState.ISOLATED
        return system_state

    @allure.step('{0} - Start health mechanism')
    def start_health_mechanism(self):
        self.start_collector()
        state = self.get_agent_status()
        if state == FortiEdrSystemState.RUNNING:
            Reporter.report("Health monitor successfully helped to bring collector service up")
        else:
            assert False, "Failed to start collector service, check what happens in logs"

    @allure.step("{0} - Install FortiEDR Collector")
    def install_collector(self,
                          version: str,
                          aggregator_ip: str,
                          aggregator_port: int = None,
                          registration_password: str = None,
                          organization: str = None):

        aggregator_port = aggregator_port or DEFAULT_AGGREGATOR_PORT
        registration_pass = registration_password or REGISTRATION_PASS
        version = version or self.get_version()
        installer_path = get_installer_path(self, version)

        logs_path = self._get_logs_path(collector=self, prefix="Installation_logs")
        Reporter.report(f"Installation logs can be found here: {logs_path}")

        cmd = generate_installation_cmd(installer_path=installer_path,
                                        agg_ip=aggregator_ip,
                                        agg_port=aggregator_port,
                                        registration_pass=registration_pass,
                                        logs_path=logs_path,
                                        organization=organization)
        self.os_station.execute_cmd(cmd=cmd, fail_on_err=True)
        wait_until_collector_pid_appears(self)
        self.update_process_id()

    @allure.step("{0} - Uninstall FortiEDR Collector")
    def uninstall_collector(self, registration_password: str = None, stop_collector: bool = False):
        registration_password = registration_password or REGISTRATION_PASS

        logs_path = self._get_logs_path(collector=self, prefix="Uninstallation_logs")
        Reporter.report(f"Installation logs can be found here: {logs_path}")

        uninstall_script_path = create_uninstallation_script(collector_agent=self,
                                                             registration_password=registration_password,
                                                             logs_file_path=logs_path)
        self.os_station.execute_cmd(cmd=uninstall_script_path, asynchronous=False)
        wait_until_collector_pid_disappears(self)
        self.update_process_id()

    @allure.step("Check if collector files exist")
    def is_collector_files_exist(self) -> bool:
        files = self.os_station.get_list_of_files_in_folder(folder_path=self.__collector_installation_path)
        if files is None or len(files) == 0:
            Reporter.report("Collector files does not exist, probably not installed anymore")
            return False

        Reporter.report("Collector files exist, probably still installed")
        return True

    @allure.step("{0} - Copy log parser to machine")
    def copy_log_parser_to_machine(self):
        """
        The role of this method is to copy the log parser to the machine.
        if log parser exist it will return the full path of log parser path, else copy from shared folder
        and return file path
        :return: full log parser file path
        """
        version = self.get_version()
        shared_drive_path = rf'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'
        desired_file_name = f'blg2log_{version}.exe'

        # check if file exist in the machine
        is_decoder_exist = self.os_station.is_path_exist(path=fr'{self.__target_logs_folder}\{desired_file_name}')
        full_decoder_file_path = fr'{self.__target_logs_folder}\{desired_file_name}'

        if not is_decoder_exist:
            target_copy_folder = self.os_station.copy_files_from_shared_folder(
                target_path_in_local_machine=self.__target_logs_folder,
                shared_drive_path=shared_drive_path,
                shared_drive_user_name=third_party_details.USER_NAME,
                shared_drive_password=third_party_details.PASSWORD,
                files_to_copy=[desired_file_name])

            full_decoder_file_path = fr'{target_copy_folder}\{desired_file_name}'

        return full_decoder_file_path

    @allure.step("{0} - Copy all .blg log files that was modified after {initial_timestamp} to C:\\ParsedLogsFolder")
    def _copy_blg_log_files_that_was_modified_after_given_timestamp_to_parsed_log_folder(self,
                                                                                         initial_timestamp: str):
        """
        the role of this method is to copy all blg .files that was modified after the initial timestamp
        :param initial_timestamp: should be in the format: 25/01/2022 16:11:38
        """

        first_time_stamp_datetime = datetime.strptime(initial_timestamp, "%d/%m/%Y %H:%M:%S")

        folders_in_logs = self.os_station.get_list_of_files_in_folder(folder_path=self.__collector_logs_folder)
        for log_folder in folders_in_logs:
            log_files_in_log_folder = self.os_station.get_list_of_files_in_folder(
                folder_path=fr'{self.__collector_logs_folder}\{log_folder}', file_suffix='.blg')
            for single_log_file in log_files_in_log_folder:

                # if file not modified after initial timestamp
                last_modified_date = self.os_station.get_file_last_modify_date(file_path=single_log_file, date_format="'u'")
                last_modified_date = last_modified_date.replace('Z', '')
                last_modified_date_time = datetime.strptime(last_modified_date, "%Y-%m-%d %H:%M:%S")

                if last_modified_date_time >= first_time_stamp_datetime:
                    self.os_station.copy_files(source=single_log_file, target=self.__target_logs_folder)

    @allure.step("{0} - Remove all log files from parsed log folder C:\\ParsedLogsFolder")
    def _remove_all_log_files_from_parsed_log_folder(self):
        if self.os_station.is_path_exist(path=fr'{self.__target_logs_folder}\*.log'):
            self.os_station.remove_file(file_path=fr'{self.__target_logs_folder}\*.log')

        if self.os_station.is_path_exist(path=fr'{self.__target_logs_folder}\*.blg'):
            try:
                self.os_station.remove_file(file_path=fr'{self.__target_logs_folder}\*.blg')
            except Exception as e:
                print(e)

    @allure.step("{0} - Remove all irrelevant blg2log parsers from C:\\ParsedLogsFolder")
    def _remove_all_irrelevant_blg2log_parsers(self):
        parsers = self.os_station.get_list_of_files_in_folder(folder_path=fr'{self.__target_logs_folder}\blg2log_*')
        current_version = self.get_version()
        if parsers is not None and len(parsers) > 0:
            for file in parsers:
                if current_version not in file:
                    self.os_station.remove_file(file_path=fr'{self.__target_logs_folder}\{file}')

    @allure.step("{0} - Clear logs")
    def clear_logs(self):
        """
        This method is used to clear all collector logs
        """

        # better to stop service since we don't know what will happen if we remove file during service writing to it.
        self.stop_collector(password='12345678')
        sub_log_folder = self.os_station.get_list_of_files_in_folder(folder_path=self.__collector_logs_folder)
        Reporter.report("Removing all files from logs folder")
        for sub_folder in sub_log_folder:
            self.os_station.remove_file(file_path=fr'{self.__collector_logs_folder}\{sub_folder}\*.blg')
        self.start_collector()

    def _prepare_parsed_logs(self, initial_timestamp: str):

        self._remove_all_log_files_from_parsed_log_folder()
        self._remove_all_irrelevant_blg2log_parsers()

        log_parser_file = self.copy_log_parser_to_machine()
        self._copy_blg_log_files_that_was_modified_after_given_timestamp_to_parsed_log_folder(
            initial_timestamp=initial_timestamp
        )

        Reporter.report("Checking if all .blg files parsed successfully")
        # extract number of blg files after copy - 1 (minus the log parser itself)
        num_blg_files = len(self.os_station.get_list_of_files_in_folder(folder_path=self.__target_logs_folder)) - 1

        # parse logs in quite mode - without waiting to prompt (no need to enter key for exit)
        self.os_station.execute_cmd(cmd=f'cd {self.__target_logs_folder} & {log_parser_file} -q')

        curr_num_of_files = len(self.os_station.get_list_of_files_in_folder(folder_path=self.__target_logs_folder)) - 1
        expected_file_num = num_blg_files * 2

        timeout = 60
        sleep_delay = 2
        start_time = time.time()
        if curr_num_of_files != expected_file_num:
            while curr_num_of_files < expected_file_num and time.time() - start_time < timeout:
                curr_num_of_files = len(
                    self.os_station.get_list_of_files_in_folder(folder_path=self.__target_logs_folder)) - 1
                time.sleep(sleep_delay)

        if curr_num_of_files != expected_file_num:
            assert False, f"Not all log files parsed within {timeout}"
        else:
            Reporter.report("all .blg files parsed successfully :)")

    @allure.step("{0} - Get logs content")
    def get_logs_content(self, file_suffix='.blg', filter_regex=None) -> dict:
        """
        This method will collect all logs content
        Args:
            filter_regex:
            file_suffix (str): files types to take into account, default is .blg
            filter_regex (str): a regex filter to apply on the content

        Returns:
            dict: a dictionary of log-file-name: content
        """
        self._prepare_parsed_logs(initial_timestamp=datetime.strftime(datetime.min, "%d/%m/%Y %H:%M:%S"))

        # for each .txt file
        log_files = self.os_station.get_list_of_files_in_folder(
            folder_path=self.__target_logs_folder, file_suffix='.log'
        )

        logs = {}
        for single_parsed_file in log_files:
            content = self.os_station.get_file_content(file_path=single_parsed_file, filter_regex=filter_regex)
            logs[single_parsed_file] = content

        return logs

    @allure.step("{0} - return logs from a given log timestamp {first_log_timestamp_to_append} as dictionary")
    def get_parsed_logs_after_specified_time_stamp(self,
                                                   first_log_timestamp_to_append: str,
                                                   file_suffix='.blg') -> Dict[str, str]:
        """
        This method will return all logs that was created after the given initial timestamp
        :param first_log_timestamp_to_append: the time stamp of the log that we want to add from (lower threshold)
        should be in the format: 25/01/2022 16:11:38
        :param file_suffix: files types to take into account, default is .blg
        """
        logs_dict_with_content = {}

        machine_timestamp_regex = r'(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+):(\d+)'
        first_time_stamp_datetime_to_append = datetime.strptime(first_log_timestamp_to_append, "%d/%m/%Y %H:%M:%S")

        self._prepare_parsed_logs(initial_timestamp=first_log_timestamp_to_append)

        # for each .txt file
        log_files = self.os_station.get_list_of_files_in_folder(
            folder_path=self.__target_logs_folder, file_suffix='.log'
        )

        for single_parsed_file in log_files:

            is_logs_exist_after_the_first_timestamp = False
            content = self.os_station.get_file_content(file_path=single_parsed_file)
            first_date_in_log_file = StringUtils.get_txt_by_regex(
                text=content, regex=f'({machine_timestamp_regex})', group=1
            )

            first_time_stamp_in_log_file_datetime = datetime.strptime(first_date_in_log_file, "%d/%m/%Y %H:%M:%S")

            if first_log_timestamp_to_append in content:
                index = content.index(first_log_timestamp_to_append)
                content = content[index:]
                is_logs_exist_after_the_first_timestamp = True
            elif first_time_stamp_in_log_file_datetime >= first_time_stamp_datetime_to_append:
                is_logs_exist_after_the_first_timestamp = True
            else:
                content_split = content.split('\n')
                for single_line in content_split:
                    line_date = StringUtils.get_txt_by_regex(
                        text=single_line, regex=f'({machine_timestamp_regex})', group=1
                    )

                    if line_date is not None:
                        if datetime.strptime(line_date, "%d/%m/%Y %H:%M:%S") > first_time_stamp_datetime_to_append:
                            first_index = content.index(line_date)
                            content = content[first_index:]
                            logs_dict_with_content[single_parsed_file] = content
                            break

            if is_logs_exist_after_the_first_timestamp:
                logs_dict_with_content[single_parsed_file] = content

        return logs_dict_with_content

    @allure.step("{0} - Append logs to report from a given log timestamp {first_log_timestamp_to_append}")
    def append_logs_to_report(self,
                              first_log_timestamp_to_append: str,
                              file_suffix='.blg'):
        """
        This method will append logs to report from the given initial timestamp
        :param first_log_timestamp_to_append: the time stamp of the log that we want to add from (lower threshold)
        should be in the format: 25/01/2022 16:11:38
        :param file_suffix: files types to take into account, default is .blg
        """
        results_dict = self.get_parsed_logs_after_specified_time_stamp(
            first_log_timestamp_to_append=first_log_timestamp_to_append,
            file_suffix=file_suffix)

        if results_dict is not None and len(results_dict) > 0:
            for file_name, file_content in results_dict.items():
                Reporter.attach_str_as_file(file_name=file_name, file_content=file_content)

    @allure.step("{0} - Create event {malware_name}")
    def create_event(self, malware_name: str = "DynamicCodeTests.exe"):
        malware_folder = rf'{third_party_details.SHARED_DRIVE_QA_PATH}\automation_ng\malware_sample'
        target_path = self.get_qa_files_path()
        target_folder = self.os_station.copy_files_from_shared_folder(
            target_path_in_local_machine=target_path, shared_drive_path=malware_folder,
            files_to_copy=[malware_name])

        pids = self.os_station.get_service_process_ids(malware_name)
        if pids is not None:
            for single_pid in pids:
                self.os_station.kill_process_by_id(pid=single_pid)

        self.os_station.execute_cmd(f'{target_folder}\\{malware_name}', asynchronous=True)

    def _get_logs_path(self, collector: CollectorAgent, prefix):
        logs_file_name = f"{prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        logs_folder = collector.os_station.create_new_folder(fr'{INSTALL_UNINSTALL_LOGS_FOLDER_PATH}')
        logs_path = fr"{logs_folder}\{logs_file_name}"
        return logs_path

    @allure.step("Create collector bootstrap file backup")
    def create_bootstrap_backup(self, reg_password, filename=None):
        bootstrap_filename = self.__bootstrap_file_name

        if filename is not None:
            bootstrap_filename = filename

        if self.get_agent_status() == FortiEdrSystemState.RUNNING:
            self.stop_collector(password=reg_password)
        else:
            Reporter.report("No need to stop the collector", INFO)

        full_path_collector_bootstrap = fr"{self.__collector_config_folder}\{bootstrap_filename}"
        expected_backup_filename = fr"{self.__collector_config_folder}\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{bootstrap_filename}"
        Reporter.report(f"Full path of bootstrap file: {full_path_collector_bootstrap}"
                        f"Expected backup filename: {expected_backup_filename}")

        result = self.os_station.execute_cmd(fr"copy {full_path_collector_bootstrap} {expected_backup_filename}")
        assert "Access is denied" not in result, f"File not copied due to access to copy file issue (usually the cause is collector not stopped). {result}"

        self.start_collector()

        return expected_backup_filename

    @allure.step("Restoring collector bootstrap file from backup")
    def restore_bootstrap_file(self, full_path_filename):
        file_to_remove = fr"{self.__collector_config_folder}\{self.__bootstrap_file_name}"
        del_command = fr"del {file_to_remove}"
        rename_command = f"rename {full_path_filename} {self.__bootstrap_file_name}"

        result = self.os_station.execute_cmd(del_command)
        logger.debug(fr"Removing file: {full_path_filename}, result: {result}")

        result = self.os_station.execute_cmd(rename_command)
        logger.debug(fr"Renaming file '{full_path_filename}', result: {result}")

    @allure.step("Simulation of EDR events configuration")
    def config_edr_simulation_tester(self, simulator_path, reg_password):
        """
        This functions configures the EDR tester for running the EDR simulation in the collector.
        """
        config_params = 'config -a'
        command = fr"python {simulator_path}\{FILENAME_EDR_TESTER} {config_params}"
        logger.info(f"Going to execute command: `{command}`")

        result = self.os_station.execute_cmd(
            cmd=command,
            return_output=True,
            fail_on_err=False,
            timeout=EDR_EVENT_TESTER_TIMEOUT,
            attach_output_to_report=True,
            asynchronous=False)
        logger.info(f"Configuration result: {result}")

        assert "Unable to open bootstrap" not in result, f"Configuration with error: {result}"

    @allure.step("Start EDR events tester")
    def start_edr_simulation_tester(self, simulator_path):
        """
        This function starts edrEventTester which is part of the EDR event simulation.
        """
        datetime_object = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        json_file_name = f'{datetime_object}-results.json'
        test_command = 'test -s json -o'
        debug_option = '-v DEBUG'
        json_results_file_path = f"{simulator_path}\\{json_file_name}"

        command = fr"python {simulator_path}\{FILENAME_EDR_TESTER} {test_command} {simulator_path}\{json_file_name} {debug_option}"

        Reporter.report(f"Running command: {command}", INFO)
        self.os_station.execute_cmd(
                cmd=command,
                return_output=True,
                fail_on_err=False,
                timeout=EDR_EVENT_TESTER_TIMEOUT,
                attach_output_to_report=True,
                asynchronous=False)

        return json_results_file_path, json_file_name

    @allure.step("EDR Event tester cleanup")
    def cleanup_edr_simulation_tester(self, edr_event_tester_path, filename):
        Reporter.report(f"Removing folder: {edr_event_tester_path}")
        self.os_station.remove_folder(folder_path=edr_event_tester_path)

        Reporter.report(rf"Removing file: {self.__qa_files_path}\{filename}")
        self.os_station.remove_file(fr"{self.__qa_files_path}\{filename}")

        Reporter.report(rf"{self.__collector_config_folder}\*.*.bak")
        self.os_station.remove_file(rf"{self.__collector_config_folder}\*.*.bak")

    @allure.step("Search for a given string {string_to_find} appears in logs after a given timestamp {first_log_date_time}")
    def is_string_in_logs(self, string_to_find: str, first_log_date_time: str) -> bool:
        logger.info(f"Get parsed logs from {first_log_date_time}")
        log_files_dict = self.get_parsed_logs_after_specified_time_stamp(
            first_log_timestamp_to_append=first_log_date_time,
            file_suffix='.blg')
        for file_name, file_content in log_files_dict.items():
            Reporter.report(f"Checking if '{string_to_find}' received in the parsed log {file_name}", logger_func=logger.info)
            result = StringUtils.get_txt_by_regex(text=file_content.lower(),
                                                  regex=string_to_find.lower(),
                                                  group=0)
            if result is not None:
                Reporter.report(f"Received from '{file_name}' log file: '{result}'", logger_func=logger.info)
                return True
        return False
