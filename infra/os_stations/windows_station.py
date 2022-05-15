import random
import re
import logging
from enum import Enum
from typing import List
import allure
from pypsexec.client import Client
from pypsexec.exceptions import SCMRException
from smbprotocol.exceptions import PipeBroken

import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.decorators import retry
from infra.common_utils import wait_for_predict_condition

from infra.os_stations.os_station_base import OsStation
from infra.os_stations.ps_py_exec_client_wrapper import PsPyExecClientWrapper
from infra.utils.utils import StringUtils

logger = logging.getLogger(__name__)

INTERVAL_STATION_KEEPALIVE = 5
WAIT_FOR_STATION_UP_TIMEOUT = 5 * 60
WAIT_FOR_STATION_DOWN_TIMEOUT = WAIT_FOR_STATION_UP_TIMEOUT


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

    @allure.step("Clean all previous SMB connections")
    def clean_all_previous_connections(self):
        try:
            self._remote_connection_session = Client(self._host_ip, username=self._user_name, password=self._password,
                                                     encrypt=self.__encrypted_connection)
            self._remote_connection_session.connect()
            self._remote_connection_session.cleanup()
            self._remote_connection_session.disconnect()
            Reporter.report("All Previous SMB connections was cleaned on the remote windows machine")

        except Exception as e:
            Reporter.report("The connections will be removed in background, can continue")

    @retry
    @allure.step("Connect To remote machine")
    def connect(self):
        try:
            # here we are using wrapper because this library creates always same service name in the remote machine
            # and we want to ensure that it will create always unique process id in case that something will get wrong
            # with the original service.
            self._connect_with_retry_on_different_encrypted_option()

        except Exception as e:
            logger.debug(f"Failed to connect to windows machine, original exception: {e}")
            Reporter.report(f"Failed to connect to windows machine, original exception: {e}")
            raise e

    def _connect_with_retry_on_different_encrypted_option(self):
        try:
            self._remote_connection_session = PsPyExecClientWrapper(self._host_ip,
                                                                    unique_connection_id=random.randint(1000000, 9999999),
                                                                    username=self._user_name,
                                                                    password=self._password,
                                                                    encrypt=self.__encrypted_connection)

            self._remote_connection_session.connect()
            self._remote_connection_session.create_service()

        except:
            self._remote_connection_session = PsPyExecClientWrapper(self._host_ip,
                                                                    unique_connection_id=random.randint(1000000,
                                                                                                        9999999),
                                                                    username=self._user_name,
                                                                    password=self._password,
                                                                    encrypt=not self.__encrypted_connection)
            self._remote_connection_session.connect()
            self._remote_connection_session.create_service()
            self.__encrypted_connection = not self.__encrypted_connection

    @retry
    @allure.step("Executing command: {cmd}")
    def execute_cmd(self, cmd: str, return_output: bool = True, fail_on_err: bool = False, timeout=180,
                    attach_output_to_report: bool = True,
                    asynchronous: bool = False):

        try:
            if self._remote_connection_session is None:
                self.connect()

            cmd = cmd.replace('\\\\', r'\\')
            logger.debug(f"Executing command: {cmd}")
            stdout_output, stderr_err_output, status_code = self._remote_connection_session.run_executable("cmd.exe",
                                                                                                           arguments=f'/c {cmd}',
                                                                                                           timeout_seconds=timeout,
                                                                                                           asynchronous=asynchronous,
                                                                                                           use_system_account=True)
            if asynchronous is True:
                return

            if return_output or attach_output_to_report:
                stdout_output = stdout_output.decode('utf-8')
                stderr_err_output = stderr_err_output.decode('utf-8')

                output = stdout_output if stdout_output != '' else stderr_err_output if stderr_err_output != '' else None
                if attach_output_to_report:
                    if output is not None and len(output) > 1000:
                        if len(output) < 2000000:
                            Reporter.attach_str_as_file(file_name=cmd, file_content=output)
                        else:
                            Reporter.report("Content is to big to attach to allure report, sorry")
                    else:
                        Reporter.report(f"command output: {output}")

                if (fail_on_err and stderr_err_output != '') or (fail_on_err and status_code != 0):
                    assert False, f"Failing because stderr was returned, {output}"

                if return_output:
                    if output is not None:
                        output = output.strip()
                    logger.debug(f"Finall Output is: {output}")
                    return output

        except SCMRException as e:
            Reporter.report("Failed to Execute command because somthing went wrong with pypsexec library connection, connecting again")
            self.connect()
            raise e

        except ConnectionAbortedError as e:
            self.connect()
            raise e

        except PipeBroken as e:
            Reporter.report("Failed to connect to windows machine, if you are connected via VPN, check that windows firewall is disabled")
            raise e

        except Exception as e:
            Reporter.report(f"Failed to execute command: {cmd} on remote windows machine, original exception: {e}")
            raise e

        finally:
            self.disconnect()

    @allure.step("Disconnect from remote machine")
    def disconnect(self):
        if self._remote_connection_session is not None:
            self._remote_connection_session.remove_service()
            self._remote_connection_session.disconnect()
            self._remote_connection_session = None

    @allure.step("Reboot")
    def reboot(self):
        uptime_sec_before_reboot = self.get_machine_uptime_seconds()
        cmd = 'shutdown -r -t 0'
        self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        self.wait_until_machine_is_unreachable()
        self.wait_until_machine_is_reachable()
        uptime_sec_after_reboot = self.get_machine_uptime_seconds()
        assert uptime_sec_after_reboot < uptime_sec_before_reboot, "Machine was not actually rebooted"

    def is_reachable(self):
        try:
            self._remote_connection_session = PsPyExecClientWrapper(self._host_ip,
                                                                    unique_connection_id=random.randint(1000000,
                                                                                                        9999999),
                                                                    username=self._user_name,
                                                                    password=self._password,
                                                                    encrypt=self.__encrypted_connection)

            self._remote_connection_session.connect()
            self._remote_connection_session.create_service()
            return True
        except:
            return False

    @allure.step("Wait until machine is reachable")
    def wait_until_machine_is_reachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_UP_TIMEOUT
        predict_condition_func = self.is_reachable
        wait_for_predict_condition(predict_condition_func=predict_condition_func,
                                   timeout_sec=timeout, interval_sec=INTERVAL_STATION_KEEPALIVE)

    @allure.step("Wait until machine is unreachable")
    def wait_until_machine_is_unreachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_DOWN_TIMEOUT

        def predict():
            result = not self.is_reachable()
            return result

        wait_for_predict_condition(predict_condition_func=predict,
                                   timeout_sec=timeout, interval_sec=INTERVAL_STATION_KEEPALIVE)

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
        available_mem = int(re.search(r'Available\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        total_mem = int(re.search(r'Total\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        usage = float((total_mem - available_mem) / total_mem)
        usage *= 100
        Reporter.report(f"Memory usage: {usage}")
        return usage

    @allure.step("Get disk usage")
    def get_disk_usage(self) -> float:
        total_disk_size = self.execute_cmd(cmd='wmic logicaldisk get size', fail_on_err=True)
        total_disk_size = int(re.search('\d+', total_disk_size).group(0))

        disk_free_space = self.execute_cmd(cmd='wmic logicaldisk get freespace')
        disk_free_space = int(re.search('\d+', disk_free_space).group(0))

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
            pid = StringUtils.get_txt_by_regex(text=row, regex=f"{service_identifier}\s+(\d+)", group=1)
            if pid is not None:
                pids.append(int(pid))

        return pids

    @allure.step("Kill process with the id: {pid}")
    def kill_process_by_id(self, pid: int):
        cmd = f"taskkill /PID {pid} /F"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Checking if path {path} exist")
    def is_path_exist(self, path: str) -> bool:

        cmd = f"IF exist {path} (echo {str(True)}) ELSE (echo {str(False)})"

        result = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False)
        if str(True) in result:
            Reporter.report("Path exist!")
            return True

        Reporter.report("Path does not exist")
        return False

    @allure.step("Get {file_path} content")
    def get_file_content(self, file_path: str) -> str:
        # cmd = f'type {file_path}'
        cmd = f'powershell "get-content -path {file_path}"'
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
        self.execute_cmd(cmd=f'net use {local_mounted_drive} /del /yes', fail_on_err=True)

    @allure.step("Mount shared drive locally")
    def mount_shared_drive_locally(self,
                                   desired_local_drive: str,
                                   shared_drive: str,
                                   user_name: str,
                                   password: str):
        self.execute_cmd(cmd=rf"net use {desired_local_drive} {shared_drive} /user:{user_name} {password}",
                         fail_on_err=True)

    @allure.step("Copy files")
    def copy_files(self, source: str, target: str):
        self.execute_cmd(cmd=f'copy {source} {target}', fail_on_err=True)

    @allure.step("Removing file {file_path}")
    def remove_file(self, file_path: str):
        self.execute_cmd(cmd=f'del /f {file_path}', fail_on_err=True)

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
        if result is None or 'file not found' in result.lower():
            return None

        files = result.split('\n')
        if file_suffix is not None:
            files = [fr'{folder_path}\{x}' for x in files if file_suffix in x]

        files = [x.replace('\r', '').replace('\n', '') for x in files]

        return files

    def __is_valid_content_to_write(self, content: str):
        if content is None or content.isspace() or content == '':
            return False
        return True

    @allure.step("Overwrite file content: {file_path}")
    def overwrite_file_content(self, content: str, file_path: str):
        rows = content.split("\n")
        cmd_builder = f"ECHO {rows[0]} > {file_path}"

        for i in range(1, len(rows)-1):
            if not self.__is_valid_content_to_write(rows[i]):
                continue

            # command line have limitation of number of characters per command so it should act as workaround
            if len(cmd_builder) <= 4000:
                cmd_builder += f"& ECHO {rows[i]} >> {file_path}"
            else:
                self.execute_cmd(cmd=cmd_builder, fail_on_err=True)
                cmd_builder = f'ECHO {rows[i]} >> {file_path}'

        if self.__is_valid_content_to_write(rows[len(rows)-1]):
            cmd_builder += f"& ECHO {rows[len(rows)-1]} >> {file_path}"
        self.execute_cmd(cmd=cmd_builder, fail_on_err=True)

    @allure.step("Copy files from shared folder to local machine")
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

            is_path_exist = self.is_path_exist(fr'X:\\')
            if not is_path_exist:
                raise Exception("Mount failed, can not copy any file from shared file")

            for single_file in files_to_copy:
                self.copy_files(source=fr'X:\\{single_file}', target=f'{target_folder}')

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
            if single_file not in files:
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
