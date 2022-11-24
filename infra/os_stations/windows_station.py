import time
from datetime import datetime
import functools
import random
import re
import logging

from enum import Enum
from typing import List
import allure

import third_party_details
from infra import common_utils
from infra.allure_report_handler.reporter import Reporter
from infra.decorators import retry
from infra.common_utils import wait_for_condition

from infra.os_stations.os_station_base import OsStation
from infra.os_stations.ps_py_exec_client_wrapper import PsPyExecClientWrapper, \
    execute_remote_command_via_ps_py_exec_context
from infra.os_stations.winrm_wrappers import SessionWinrmWrapper
from infra.utils.utils import StringUtils
from infra.os_stations.os_station_base import EXTRACT_EDR_EVENT_TESTER_TIMEOUT, MAX_WAIT_FOR_FILE_TO_APPEAR

logger = logging.getLogger(__name__)

INTERVAL_STATION_KEEPALIVE = 5
WAIT_FOR_STATION_UP_TIMEOUT = 5 * 60
WAIT_FOR_STATION_DOWN_TIMEOUT = WAIT_FOR_STATION_UP_TIMEOUT
SEVEN_ZIP_APPLICATION_PATH = "C:\\Program Files\\7-Zip"


class WindowsServiceStartTypeEnum(Enum):
    BOOT = 'boot' # Specifies a device driver that is loaded by the boot loader.
    SYSTEM = 'system' # Specifies a device driver that is started during kernel initialization.
    AUTO = 'auto' # Specifies a service that automatically starts each time the computer is restarted and runs even if no one logs on to the computer.
    DEMAND = 'demand' # Specifies a service that must be started manually. This is the default value if
    DISABLED = 'disabled' # Specifies a service that cannot be started. To start a disabled service, change the start type to some other value.
    DELAYED_AUTO = 'delayed-auto' # Specifies a service that starts automatically a short time after other auto services are started.


class WindowsStation(OsStation):

    def __init__(self, host_ip, user_name, password):
        self.__encrypted_connection = True
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password)

    def _init_os_details(self):
        self._enable_win_rm()
        super()._init_os_details()

    @allure.step("Enable winrm on windows host")
    def _enable_win_rm(self):
        try:
            # try to perform ipconfig command via winrm library according to current implementation
            self.execute_cmd(cmd='ipconfig',
                             return_output=False,
                             fail_on_err=True,
                             attach_output_to_report=False,
                             use_pa_py_exec_connection=False,
                             asynchronous=False)
        except:
            self.execute_cmd(cmd='powershell "Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private"',
                             return_output=False,
                             fail_on_err=True,
                             attach_output_to_report=True,
                             use_pa_py_exec_connection=True,
                             asynchronous=False)

            # in case of ex excetion, enable winrm on windows host by using paexec library
            self.execute_cmd(cmd='winrm qc -q',
                             return_output=False,
                             fail_on_err=True,
                             attach_output_to_report=True,
                             use_pa_py_exec_connection=True,
                             asynchronous=False)

            self.execute_cmd(cmd='winrm set winrm/config/service @{AllowUnencrypted="true"}',
                             return_output=False,
                             fail_on_err=True,
                             attach_output_to_report=True,
                             use_pa_py_exec_connection=True,
                             asynchronous=False)

            self.execute_cmd(cmd='winrm set winrm/config/service/auth @{Basic="true"}',
                             return_output=False,
                             fail_on_err=True,
                             attach_output_to_report=True,
                             use_pa_py_exec_connection=True,
                             asynchronous=False)

    @allure.step("Connect To remote machine")
    def connect(self, force: bool = False):
        if self._remote_connection_session is None or force:
            self._remote_connection_session = SessionWinrmWrapper(f'http://{self.host_ip}',
                                                                  auth=(self.user_name, self.password))

    @allure.step("Disconnect from remote machine")
    def disconnect(self):
        raise NotImplementedError("Disconnect from remote machine not implemented yet.")

    @allure.step("Executing command: {cmd}")
    def execute_cmd(self,
                    cmd: str,
                    return_output: bool = True,
                    fail_on_err: bool = False,
                    timeout=180,
                    attach_output_to_report: bool = True,
                    asynchronous: bool = False,
                    use_pa_py_exec_connection: bool = False):
        if self._remote_connection_session is None:
            self.connect()

        cmd = cmd.replace('\\\\', r'\\')

        logger.debug(f"Executing command: {cmd}")

        # add here more logic regarding paexec library
        std_out = None
        std_err = None
        status_code = None

        if use_pa_py_exec_connection or asynchronous:
            with execute_remote_command_via_ps_py_exec_context(host_ip=self.host_ip,
                                                               user_name=self.user_name,
                                                               password=self.password,
                                                               timeout=timeout,
                                                               cmd=cmd,
                                                               asynchronous=asynchronous) as result:
                if asynchronous:
                    return
                
                std_out, std_err, status_code = result[0], result[1], result[2]

        else:
            result = self._remote_connection_session.run_cmd_with_timeout(command=cmd, timeout=timeout)
            std_out = result.std_out.decode('utf-8')
            std_err = result.std_err.decode('utf-8')
            status_code = result.status_code

        output = std_out if std_out is not None and std_out != '' else None
        if output is None or output == '':
            if std_err is not None and std_err != '':
                output = std_err

        if attach_output_to_report:
            if output is not None and len(output) > 1000:
                if len(output) < 2000000:
                    Reporter.attach_str_as_file(file_name=cmd, file_content=output)
                else:
                    Reporter.report("Content is to big to attach to allure report, sorry")
            else:
                Reporter.report(f"command output: {output}")

        if (fail_on_err and std_err != '') or (
                fail_on_err and status_code != 0 and 'windows 7' not in self.os_name.lower()):
            assert False, f"Failing because stderr was returned, {output}"

        if return_output:
            if output is not None:
                output = output.strip()
                if len(output) < 1000:
                    logger.debug(f"Final Output is: {output}")
                else:
                    logger.debug(f"command {cmd} output size is: {len(output)} - skip write to log")

            return output

    @allure.step("Reboot")
    def reboot(self):
        cmd = 'shutdown -r -t 0'
        self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        self.wait_until_machine_is_unreachable()
        self.wait_until_machine_is_reachable()

    def is_reachable(self):
        try:
            self.execute_cmd(cmd='ipconfig',
                             return_output=False,
                             fail_on_err=True,
                             use_pa_py_exec_connection=False,
                             asynchronous=False)
            return True
        except:
            return False

    @allure.step("Wait until machine is reachable")
    def wait_until_machine_is_reachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_UP_TIMEOUT
        predict_condition_func = self.is_reachable
        wait_for_condition(condition_func=predict_condition_func, timeout_sec=timeout,
                           interval_sec=INTERVAL_STATION_KEEPALIVE, condition_msg="VM is reachable")

    @allure.step("Wait until machine is unreachable")
    def wait_until_machine_is_unreachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_DOWN_TIMEOUT

        def predict():
            result = not self.is_reachable()
            return result

        wait_for_condition(condition_func=predict, timeout_sec=timeout,
                           interval_sec=INTERVAL_STATION_KEEPALIVE, condition_msg="VM is unreachable")

    @allure.step("Stop service {service_name}")
    def stop_service(self, service_name: str) -> str:
        cmd = f'powershell "Stop-service {service_name}"'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("Start service {service_name}")
    def start_service(self, service_name: str) -> str:
        cmd = f'powershell "Start-service {service_name}"'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True, )
        return result

    @allure.step("Get OS architecture")
    def get_os_architecture(self):
        cmd = 'wmic os get osarchitecture'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True)
        result = result.replace('\r', '').replace('\n', '')
        arch = StringUtils.get_txt_by_regex(text=result, regex=r'OSArchitecture\s+(.+)', group=1)
        return arch

    @allure.step("Get hostname")
    def get_hostname(self):
        result = self.execute_cmd(cmd='hostname', fail_on_err=True, return_output=True)
        return result

    @allure.step("Get OS version")
    def get_os_version(self):
        cmd = 'systeminfo | findstr /B /C:"OS Version"'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True)
        os_ver = StringUtils.get_txt_by_regex(text=result, regex=r'OS\s+Version:\s+(.+)', group=1)
        return os_ver

    @allure.step("Get current windows machine date time")
    def get_current_machine_datetime(self, date_format="-UFormat '%d/%m/%Y %T'"):
        cmd = f"""powershell "Get-Date {date_format}"""
        result = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @retry
    @allure.step("Get OS name")
    def get_os_name(self):
        # takes time to invoke this command, so if you are working from home or have high latency the result can be None
        cmd = 'systeminfo | findstr /B /C:"OS Name"'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True)
        os_ver = StringUtils.get_txt_by_regex(text=result, regex=r'OS\s+Name:\s+(.+)', group=1)
        return os_ver

    @allure.step("Get CPU usage")
    def get_cpu_usage(self) -> float:
        cmd = "wmic cpu get loadpercentage /format:value"
        cpu_info = self.execute_cmd(cmd=cmd, fail_on_err=True)
        cpu = re.search(r'LoadPercentage=(\d+)', cpu_info).group(1)
        Reporter.report(f'CPU usage: {cpu}')
        return float(cpu)

    @allure.step("Get memory usage")
    def get_memory_usage(self) -> float:
        cpu_info = self.execute_cmd(cmd='systeminfo | find /I "Physical Memory"', fail_on_err=True)
        available_mem = int(
            re.search(r'Available\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        total_mem = int(re.search(r'Total\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        usage = float((total_mem - available_mem) / total_mem)
        usage *= 100
        Reporter.report(f"Memory usage: {usage}")
        return usage

    @allure.step("Get disk usage")
    def get_disk_usage(self) -> float:
        total_disk_size = self.execute_cmd(cmd='wmic logicaldisk get size', fail_on_err=True)
        total_disk_size = int(re.search(r'\d+', total_disk_size).group(0))

        disk_free_space = self.execute_cmd(cmd='wmic logicaldisk get freespace')
        disk_free_space = int(re.search(r'\d+', disk_free_space).group(0))

        usage = float((total_disk_size - disk_free_space) / total_disk_size)
        usage *= 100
        Reporter.report(f"Disk usage: {usage}")
        return usage

    @allure.step("Get {service_identifier} service process IDs")
    def get_service_process_ids(self, service_identifier: str) -> List[int]:
        result = self.execute_cmd(cmd=f'TASKLIST | find "{service_identifier}"')
        if result is None:
            return None
        result_splitted = result.split('\r\n')
        pids = []
        for row in result_splitted:
            pid = StringUtils.get_txt_by_regex(text=row, regex=fr"{service_identifier}\s+(\d+)", group=1)
            if pid is not None:
                pids.append(int(pid))

        return pids

    @allure.step("Kill process with the id: {pid}")
    def kill_process_by_id(self, pid: int):
        cmd = f"taskkill /PID {pid} /F"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Checking if path {path} exist")
    def is_path_exist(self, path: str, use_pa_py_exec_connection=False) -> bool:

        cmd = f"IF exist {path} (echo {str(True)}) ELSE (echo {str(False)})"

        result = self.execute_cmd(cmd=cmd,
                                  return_output=True,
                                  fail_on_err=False,
                                  use_pa_py_exec_connection=use_pa_py_exec_connection)
        if str(True) in result:
            Reporter.report("Path exist!")
            return True

        Reporter.report("Path does not exist")
        return False

    @allure.step("Get {file_path} content")
    def get_file_content(self, file_path: str, filter_regex: str = None) -> str:
        # cmd = f'type {file_path}'
        cmd = f'powershell "get-content -path {file_path}"'
        if filter_regex is not None:
            cmd = f'powershell "select-string -pattern "{filter_regex}" -path {file_path} | ForEach-Object Line"'
        file_content = self.execute_cmd(cmd=cmd,
                                        return_output=True,
                                        fail_on_err=True,
                                        attach_output_to_report=False,
                                        timeout=5 * 60)
        return file_content

    @allure.step("Create new folder {folder_path}")
    def create_new_folder(self, folder_path: str) -> str:
        is_path_exist = self.is_path_exist(path=folder_path)

        if is_path_exist:
            return folder_path

        self.execute_cmd(cmd=f'mkdir {folder_path}', return_output=False, fail_on_err=True)
        return folder_path

    @allure.step("Delete all mounted drives")
    def remove_mounted_drive(self, local_mounted_drive: str = '*'):
        self.execute_cmd(cmd=f'net use {local_mounted_drive} /del /yes',
                         fail_on_err=True,
                         use_pa_py_exec_connection=True)

    @allure.step("Mount shared drive locally")
    def mount_shared_drive_locally(self,
                                   desired_local_drive: str,
                                   shared_drive: str,
                                   user_name: str,
                                   password: str):
        command = rf"net use {desired_local_drive} {shared_drive} /user:{user_name} {password}"
        logger.info(f"Going to execute command: {command}")
        self.execute_cmd(cmd=command, fail_on_err=True, use_pa_py_exec_connection=True)

    @allure.step("Copy folder")
    def copy_folder(self, source: str, target: str, use_pa_py_exec_connection: bool = False):
        cmd = f"Xcopy {source} {target} /e /i /c /y"
        self.execute_cmd(cmd=cmd, fail_on_err=True, use_pa_py_exec_connection=use_pa_py_exec_connection)

    @allure.step("Copy files")
    def copy_files(self, source: str, target: str, use_pa_py_exec_connection: bool = False):
        self.execute_cmd(cmd=f'copy {source} {target}',
                         fail_on_err=True,
                         use_pa_py_exec_connection=use_pa_py_exec_connection)

    @allure.step("Removing file {file_path}")
    def remove_file(self, file_path: str, force: bool = True, safe: bool = False):
        cmd = f'del # {file_path}'
        if force:
            cmd = cmd.replace("#", '/f')
        else:
            cmd = cmd.replace(" #", '')

        output = self.execute_cmd(cmd=cmd, fail_on_err=not safe, return_output=True)
        return output

    @allure.step("Removing folder {folder_path}")
    def remove_folder(self, folder_path: str):
        self.execute_cmd(cmd=f'rmdir /s /q {folder_path}', fail_on_err=True)

    @allure.step("Get list of files inside {folder_path} with the suffix {file_suffix}")
    def get_list_of_files_in_folder(self,
                                    folder_path: str,
                                    file_suffix: str = None) -> List[str]:

        if " " in folder_path:
            folder_path = f'"{folder_path}"'
        result = self.execute_cmd(cmd=f'dir /b {folder_path}', return_output=True, fail_on_err=False)
        if result is None or 'file not found' in result.lower() or 'the system cannot find the file specified' in result.lower():
            return None

        files = result.split('\n')
        if file_suffix is not None:
            files = [fr'{folder_path}\{x}' for x in files if file_suffix in x]

        files = [x.replace('\r', '').replace('\n', '') for x in files]

        return files

    def get_files_details_in_folder(self,
                                    folder_path: str,
                                    desired_files_suffix: str,
                                    ignore_file_suffix: str = None,
                                    ordered_by_date_time: bool = True) -> List[dict]:
        """
        Get files inside {folder path} include name, size and datetime, sorted by timestamp
        """

        if desired_files_suffix is None:
            raise Exception("desired_files_suffix - must pass this param - for example, .json")

        command = rf'dir {folder_path}# | find "{desired_files_suffix}"'
        if ordered_by_date_time:
            command = command.replace('#', ' /OD') # sorted by timestamp
        else:
            command = command.replace('#', '')

        date_index = 0
        time_index = 1
        pm_am_index = 2
        size_index = 3
        name_index = 4
        logger.info(f"Get details of the json files inside {folder_path}: size, name and datetime")
        result = self.execute_cmd(cmd=command)

        files_details = result.split('\r\n')
        logger.debug(f"{folder_path} contains these files details {files_details}")
        formatted_files_details = []
        for file_details in files_details:
            formatted_file_details = re.split(r'\s+', file_details)
            if ignore_file_suffix not in formatted_file_details[name_index]:
                file_details_dict = {}
                file_create_date = f"{formatted_file_details[date_index]} {formatted_file_details[time_index]} {formatted_file_details[pm_am_index]}"
                file_details_dict["file_datetime"] = datetime.strptime(f"{file_create_date}", '%m/%d/%Y %I:%M %p')
                file_details_dict["file_name"] = formatted_file_details[name_index]
                file_details_dict["file_size"] = int(formatted_file_details[size_index].replace(",", ""))
                formatted_files_details.append(file_details_dict)

        return formatted_files_details

    def __is_valid_content_to_write(self, content: str):
        if content is None or content.isspace() or content == '':
            return False
        return True

    @allure.step("Overwrite file content: {file_path}")
    def overwrite_file_content(self, content: str, file_path: str, safe: bool = False):
        rows = content.split("\n")
        cmd_builder = f"ECHO {rows[0]} > {file_path}"

        for i in range(1, len(rows) - 1):
            if not self.__is_valid_content_to_write(rows[i]):
                continue

            # command line have limitation of number of characters per command so it should act as workaround
            if len(cmd_builder) <= 4000:
                cmd_builder += f"& ECHO {rows[i]} >> {file_path}"
            else:
                self.execute_cmd(cmd=cmd_builder, fail_on_err=True)
                cmd_builder = f'ECHO {rows[i]} >> {file_path}'

        if self.__is_valid_content_to_write(rows[len(rows) - 1]):
            cmd_builder += f"& ECHO {rows[len(rows) - 1]} >> {file_path}"

        output = self.execute_cmd(cmd=cmd_builder, fail_on_err=not safe, return_output=True)
        return output

    @allure.step("append text to file {file_path}")
    def append_text_to_file(self, content: str, file_path: str):
        raise Exception("Not implemented yet")

    @allure.step("Copy files from shared folder to local machine")
    @retry
    def copy_files_from_shared_folder(self,
                                      target_path_in_local_machine: str,
                                      shared_drive_path: str,
                                      files_to_copy: List[str],
                                      shared_drive_user_name: str = third_party_details.USER_NAME,
                                      shared_drive_password: str = third_party_details.PASSWORD):
        """
        The role of this method is to copy files from the shared folder to target folder in the remote station
        :param target_path_in_local_machine: target folder for copied files
        :param shared_drive_path: path in shared drive folder, must be a path to folder
        :param shared_drive_user_name: user name
        :param shared_drive_password: password
        :param files_to_copy: list of file names to copy, if you want to copy all files in folder, pass ['*']
        :return: folder path of the copied files
        """

        target_folder = self.create_new_folder(folder_path=target_path_in_local_machine)
        files_exist = self.is_files_exist(target_path_in_local_machine, files_to_copy)
        if files_exist:
            return target_folder
        try:
            self.remove_mounted_drive()

            if "Windows 7" in self._os_name and not shared_drive_user_name.startswith(
                    "ensilo\\") and 'ens-fs01' in shared_drive_path:
                shared_drive_user_name = fr"ensilo\{shared_drive_user_name}"

            self.mount_shared_drive_locally(desired_local_drive='X:',
                                            shared_drive=shared_drive_path,
                                            user_name=shared_drive_user_name,
                                            password=shared_drive_password)

            is_path_exist = self.is_path_exist(path=fr'X:\\', use_pa_py_exec_connection=True)
            if not is_path_exist:
                raise Exception("Mount failed, can not copy any file from shared file")

            for single_file in files_to_copy:
                self.copy_files(source=fr'X:\\{single_file}',
                                target=f'{target_folder}',
                                use_pa_py_exec_connection=True)

            files_exist = self.is_files_exist(target_path_in_local_machine, files_to_copy)
            if not files_exist:
                raise Exception(f"files copy failed in {self.host_ip}")

            return target_folder

        finally:
            self.remove_mounted_drive()

    @allure.step("Move file {file_name} to {target_folder}")
    def move_file(self, file_name: str, target_folder: str):
        cmd = rf"move {file_name} {target_folder}"
        self.execute_cmd(cmd=cmd, fail_on_err=True, attach_output_to_report=True)

    def is_files_exist(self, target_path, files_to_copy):
        files = self.get_list_of_files_in_folder(target_path)

        if files is None or files == []:
            return False

        for single_file in files_to_copy:
            if single_file not in files and not None:
                return False
        return True

    @allure.step("Get file last modify date")
    def get_file_last_modify_date(self, file_path: str, date_format: str = "'u'") -> str:
        cmd = f"""powershell "(Get-Item "{file_path}").LastWriteTime.GetDateTimeFormats({date_format})"""
        result = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("Change service {service_name} start type to {service_start_type}")
    def change_service_start_type(self, service_name: str, service_start_type: WindowsServiceStartTypeEnum):
        cmd = f'sc config {service_name} start={service_start_type.value}'
        result = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("Get current windows machine uptime in seconds")
    def get_machine_uptime_seconds(self):
        cmd = 'powershell "[int]((get-date)-' \
              '((Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime)).TotalSeconds"'
        uptime_sec = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        Reporter.report(f"Uptime sec is {uptime_sec}")
        return int(uptime_sec)

    @allure.step("Rename host name")
    def rename_hostname(self, host_name: str):
        host_name = "Computer%RANDOM%" if host_name is None else host_name
        self.execute_cmd(cmd=f'wmic computersystem where name="%COMPUTERNAME%" call rename name={host_name}')
        self.reboot()

    @allure.step("Wait for file to appear in specified folder")
    def wait_for_file_to_appear_in_specified_folder(self, file_path, file_name, timeout=None):
        max_timeout = timeout

        if timeout is None:
            max_timeout = MAX_WAIT_FOR_FILE_TO_APPEAR

        predict_condition_func = functools.partial(self.is_files_exist, target_path=file_path, files_to_copy=[file_name])

        common_utils.wait_for_condition(
            condition_func=predict_condition_func,
            timeout_sec=max_timeout,
            interval_sec=INTERVAL_STATION_KEEPALIVE,
            condition_msg=f"File '{file_name}' exists in {file_path}")

    @allure.step("Extracting compressed file")
    def extract_compressed_file(self, file_path_to_extract, file_name):
        """This function using 7-zip which is should be installed in the VM templates in advance.
        The extraction will be at the same copied path.

        file_path: str - Path to file to be extracted
        file_name: str - The file name to extract

        Returns
        ----
        output_path: str - The output path of the extracted files
        """
        output_path = fr"{file_path_to_extract}\{file_name.split('.')[0]}"

        command = fr"powershell Expand-Archive {file_path_to_extract}\{file_name} -DestinationPath {output_path} -Force -Verbose"
        logger.info(f"Going to execute command: {command}")

        Reporter.report(f"Extracting files with command: {command}")
        command_output = self.execute_cmd(
            cmd=command,
            return_output=True,
            fail_on_err=False,
            timeout=EXTRACT_EDR_EVENT_TESTER_TIMEOUT,
            attach_output_to_report=False,
            asynchronous=False)

        Reporter.report(f"Command Expand-Archive output:\n {command_output}")

        return output_path

    @allure.step("Copy folder with files from network")
    def copy_folder_with_files_from_network(self,
                                            local_path: str,
                                            network_path: str,
                                            shared_drive_user_name: str = third_party_details.USER_NAME,
                                            shared_drive_password: str = third_party_details.PASSWORD):
            """ This function is about copy folder with its files from the network path. """

            target_folder = self.create_new_folder(folder_path=local_path)

            try:
                self.remove_mounted_drive()

                if "Windows 7" in self._os_name and not shared_drive_user_name.startswith(
                        "ensilo\\") and 'ens-fs01' in network_path:
                    shared_drive_user_name = fr"ensilo\{shared_drive_user_name}"

                self.mount_shared_drive_locally(desired_local_drive='X:',
                                                shared_drive=network_path,
                                                user_name=shared_drive_user_name,
                                                password=shared_drive_password)

                is_path_exist = self.is_path_exist(path=fr'X:\\', use_pa_py_exec_connection=True)
                if not is_path_exist:
                    raise Exception("Mount failed, can not copy any file from shared file")

                self.copy_folder(source=fr'X:\\', target=target_folder, use_pa_py_exec_connection=True)

                return target_folder

            finally:
                self.remove_mounted_drive()

    @allure.step("Copy folder with files to network")
    def copy_folder_with_files_to_network(self,
                                            local_path: str,
                                            network_path: str,
                                            shared_drive_user_name: str = third_party_details.USER_NAME,
                                            shared_drive_password: str = third_party_details.PASSWORD):
            """ This function is about copy folder with its files to the network path. """

            try:
                self.remove_mounted_drive()

                if "Windows 7" in self._os_name and not shared_drive_user_name.startswith(
                        "ensilo\\") and 'ens-fs01' in network_path:
                    shared_drive_user_name = fr"ensilo\{shared_drive_user_name}"

                self.mount_shared_drive_locally(desired_local_drive='X:',
                                                shared_drive=network_path,
                                                user_name=shared_drive_user_name,
                                                password=shared_drive_password)

                is_path_exist = self.is_path_exist(path=fr'X:\\', use_pa_py_exec_connection=True)
                if not is_path_exist:
                    raise Exception("Mount failed, can not copy any file from shared file")

                try:
                    self.copy_folder(source=local_path, target=fr'X:\\', use_pa_py_exec_connection=True)
                except Exception as e:
                    assert False, e

                return network_path

            finally:
                self.remove_mounted_drive()

    @allure.step("Check if {path} is file")
    def is_folder(self, path: str) -> bool:
        cmd = f'powershell "(Get-Item {path}) -is [System.IO.DirectoryInfo]"'
        output = self.execute_cmd(cmd=cmd,
                                  return_output=True,
                                  fail_on_err=True,
                                  attach_output_to_report=True,
                                  asynchronous=False)
        if 'true' in output.lower():
            return True

        return False

    @allure.step("Check if {path} is folder")
    def is_file(self, path: str) -> bool:
        return not self.is_folder(path=path)
