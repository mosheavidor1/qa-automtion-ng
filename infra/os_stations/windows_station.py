import re
from typing import List

import allure

from pypsexec.client import Client

from infra.allure_report_handler.reporter import Reporter

from infra.os_stations.os_station_base import OsStation
from infra.utils.utils import StringUtils


class WindowsStation(OsStation):

    def __init__(self,
                 host_ip,
                 user_name,
                 password):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password)

    def connect(self):
        if self._remote_connection_session is None:
            try:
                self._remote_connection_session = Client(self._host_ip, username=self._user_name, password=self._password, encrypt=True)
                self._remote_connection_session.connect()
                self._remote_connection_session.create_service()

            except Exception as e:
                Reporter.report(f"Failed to connect to windows machine, original exception: {e}")
                raise e

    @allure.step("Executing command: {cmd}")
    def execute_cmd(self, cmd: str, return_output: bool = True, fail_on_err: bool = False, timeout=180,
                    attach_output_to_report: bool = True,
                    asynchronous: bool = False):

        try:
            if self._remote_connection_session is None:
                self.connect()

            cmd = cmd.replace('\\\\', r'\\')
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
                        Reporter.attach_str_as_file(file_name=cmd, file_content=output)
                    else:
                        Reporter.report(f"command output: {output}")

                if (fail_on_err and stderr_err_output != '') or (fail_on_err and status_code != 0):
                    assert False, "Failing because stderr was returned"

                if return_output:
                    if output is not None:
                        output = output.strip()
                    return output

        except Exception as e:
            Reporter.report(f"Failed to execute command: {cmd} on remote windows machine, original exception: {e}")
            raise e

    @allure.step("Disconnect from remote machine")
    def disconnect(self):
        self._remote_connection_session.disconnect()

    @allure.step("Get OS architecture")
    def get_os_architecture(self):
        cmd = 'wmic os get osarchitecture'
        result = self.execute_cmd(cmd)
        result = result.replace('\r', '').replace('\n', '')
        arch = StringUtils.get_txt_by_regex(text=result, regex=r'OSArchitecture\s+(.+)', group=1)
        return arch

    @allure.step("Get OS versuib")
    def get_os_version(self):
        cmd = 'systeminfo | findstr /B /C:"OS Version"'
        result = self.execute_cmd(cmd)
        os_ver = StringUtils.get_txt_by_regex(text=result, regex=r'OS\s+Version:\s+(.+)', group=1)
        return os_ver

    @allure.step("Get OS name")
    def get_os_name(self):
        cmd = 'systeminfo | findstr /B /C:"OS Name"'
        result = self.execute_cmd(cmd)
        result = self.execute_cmd(cmd)
        os_ver = StringUtils.get_txt_by_regex(text=result, regex=r'OS\s+Name:\s+(.+)', group=1)
        return os_ver

    @allure.step("Get CPU usage")
    def get_cpu_usage(self) -> float:
        cpu_info = self.execute_cmd(cmd="wmic cpu get loadpercentage /format:value")
        cpu = re.search(r'LoadPercentage=(\d+)', cpu_info).group(1)
        Reporter.report(f'CPU usage: {cpu}')
        return float(cpu)

    @allure.step("Get memory usage")
    def get_memory_usage(self) -> float:
        cpu_info = self.execute_cmd(cmd='systeminfo | find /I "Physical Memory"')
        available_mem = int(re.search(r'Available\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        total_mem = int(re.search(r'Total\s+Physical\s+Memory:\s+(\d+,\d+)', cpu_info).group(1).replace(',', ''))
        usage = float((total_mem - available_mem) / total_mem)
        usage *= 100
        Reporter.report(f"Memory usage: {usage}")
        return usage

    @allure.step("Get disk usage")
    def get_disk_usage(self) -> float:
        total_disk_size = self.execute_cmd(cmd='wmic logicaldisk get size')
        total_disk_size = int(re.search('\d+', total_disk_size).group(0))

        disk_free_space = self.execute_cmd(cmd='wmic logicaldisk get freespace')
        disk_free_space = int(re.search('\d+', disk_free_space).group(0))

        usage = float((total_disk_size - disk_free_space) / total_disk_size)
        usage *= 100
        Reporter.report(f"Disk usage: {usage}")
        return usage

    @allure.step("Get {service_name} service process ID")
    def get_process_id(self, service_name: str) -> int:
        result = self.execute_cmd(f'TASKLIST | find "{service_name}"')

        if result is None:
            return None

        match = re.search(f"{service_name}\s+(\d+)", result)
        if match is None:
            return None

        process_id = re.search(f"{service_name}\s+(\d+)", result).group(1)
        return int(process_id)

    @allure.step("Checking if file {path} exist")
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
        if not self.is_path_exist(path=file_path):
            return None

        cmd = f'type {file_path}'
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
    def remove_all_mounted_drives(self):
        self.execute_cmd(cmd='net use * /del /yes', fail_on_err=True)

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
        self.execute_cmd(cmd=f'del /f {file_path}')

    @allure.step("Get list of files inside {folder_path} with the suffix {file_suffix}")
    def get_list_of_files_in_folder(self,
                                    folder_path: str,
                                    file_suffix: str = None) -> List[str]:

        if " " in folder_path:
            folder_path = f'"{folder_path}"'
        result = self.execute_cmd(cmd=f'dir /b {folder_path}', return_output=True, fail_on_err=False)
        if result is None:
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

