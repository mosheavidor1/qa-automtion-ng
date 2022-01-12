import re

import allure
import paramiko

from infra.allure_report_handler.reporter import Reporter
from infra.os_stations.os_station_base import OsStation
from infra.utils.utils import StringUtils


class LinuxStation(OsStation):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str):
        OsStation.__init__(self,
                           host_ip=host_ip,
                           user_name=user_name,
                           password=password)

    def connect(self):
        if self._remote_connection_session is None:
            try:
                self._remote_connection_session = paramiko.SSHClient()
                self._remote_connection_session.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
                self._remote_connection_session.connect(hostname=self.host_ip, username=self.user_name, password=self.password)
            except Exception as e:
                Reporter.report(f'Failed to establish SSH connection, original exception: {e}')
                raise e
        else:
            Reporter.report(f'Already connected to SSH (relevant object initiated), check why the connection failed')

    @allure.step("Disconnect from remote machine")
    def disconnect(self):
        self._remote_connection_session.close()

    def __escape_ansi(self, line):
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)

    @allure.step("Executing command: {cmd}")
    def execute_cmd(self, cmd: str, return_output: bool = True, fail_on_err: bool = False, timeout: int = 180,
                    attach_output_to_report: bool = True, asynchronous: bool = False):

        if asynchronous:
            raise Exception("Can not execute asynchronous command via ssh with paramiko library")

        try:
            if self._remote_connection_session is None:
                self.connect()

            stdin, stdout, stderr = self._remote_connection_session.exec_command(command=cmd, timeout=timeout)

            if return_output or attach_output_to_report:
                stdout_output = stdout.read()
                stdout_output = stdout_output.decode('utf-8')

                stderr_err_output = stderr.read()
                stderr_err_output = stderr_err_output.decode('utf-8')

                output = stdout_output if stdout_output != '' else stderr_err_output if stderr_err_output != '' else None
                if output is not None:
                    output = self.__escape_ansi(output).strip()

                if attach_output_to_report:
                    Reporter.report(f"command output: {output}")

                if fail_on_err and stderr_err_output != '':
                    assert False, "Failing because stderr was returned"

                if return_output:
                    return output

        except Exception as e:
            Reporter.report(f'Failed to execute command {cmd} on remote Linux machine, original exception: {e}')
            raise e

    def get_os_architecture(self):
        cmd = 'arch'
        result = self.execute_cmd(cmd=cmd, return_output=True)
        return result

    def get_os_version(self):
        cmd = 'hostnamectl | grep -i "Kernel"'
        result = self.execute_cmd(cmd=cmd, return_output=True)
        ver = StringUtils.get_txt_by_regex(text=result, regex='Kernel:\s+(.+)', group=1)
        return ver

    def get_os_name(self):
        cmd = 'hostnamectl | grep -i "Operating System"'
        result = self.execute_cmd(cmd=cmd, return_output=True)
        os_name = StringUtils.get_txt_by_regex(text=result, regex='Operating\s+System:\s+(.+)', group=1)
        return os_name

    @allure.step("Get number of rows in file: {file_path}")
    def get_number_of_lines_in_file(self, file_path):
        cmd = f"wc -l < {file_path}"
        result = self.execute_cmd(cmd=cmd)
        result = re.findall('\d+', result)
        if len(result) != 1:
            raise Exception("Failed to extract number of rows from file, check if the command is correct")
        return int(result[0])

    @allure.step("Get file content of the file {file_path}")
    def get_file_content(self, file_path):
        cmd = f"cat {file_path}"
        output = self.execute_cmd(cmd=cmd)
        return output

    @allure.step("Get file content within range")
    def get_file_content_within_range(self, file_path, start_index, end_index):
        if start_index == end_index or start_index > end_index:
            return ""

        cmd = f"sed -n '{str(start_index)},{str(end_index)}p; {str(end_index+1)}q' {file_path}"
        output = self.execute_cmd(cmd=cmd)
        return output

    @allure.step("Get list of files inside {folder_path} with the suffix {file_suffix}")
    def get_list_of_files_in_folder(self,
                                    folder_path: str,
                                    file_suffix: str = None):

        result = self.execute_cmd(f'ls {folder_path}')
        files = result.split('\n')
        if file_suffix is not None:
            files = [f'{folder_path}/{x}' for x in files if file_suffix in x]

        return files

    @allure.step("Combine multiple text files into one file")
    def combine_text_file_into_single_file(self,
                                           files: [str],
                                           target_folder: str,
                                           combined_file_name: str):
        cmd = f'cat '
        for single_file in files:
            cmd += f'{single_file } '

        cmd += f'> {target_folder}/{combined_file_name}'
        self.execute_cmd(cmd=cmd)

    @allure.step("Clear file content: file_path={file_path}")
    def clear_file_content(self, file_path: str):
        cmd = f'cat /dev/null > {file_path}'
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Get CPU usage")
    def get_cpu_usage(self) -> float:
        info = self.execute_cmd("top -b -n 1")
        cpu_usage = float(str(info).split("%Cpu(s):  ")[1].split(" us")[0])
        Reporter.report(f"CPU usage: {cpu_usage}%")
        return cpu_usage

    @allure.step("Get memory usage")
    def get_memory_usage(self) -> float:
        info = self.execute_cmd("free")
        memory_total = self.execute_cmd("free | grep Mem: | awk '{print $2}'")
        memory_used = self.execute_cmd("free | grep Mem: | awk '{print $3}'")
        mem_usage = float(int(memory_used)/int(memory_total)) * 100
        Reporter.report(f"Memory usage: {mem_usage}")
        return mem_usage

    @allure.step("Get disk usage")
    def get_disk_usage(self) -> float:
        output = self.execute_cmd("df -h / | awk '{print $5}'")
        results = re.findall(r'\d+', output)
        if results is None or len(results) != 1:
            Reporter.report("Can not extract disk usage, please look at the command output")

        disk_usage = float(results[0])
        Reporter.report(f"Disk usage: {disk_usage}")

        return disk_usage

    @allure.step("Get {service_name} service process ID")
    def get_process_id(self, service_name: str) -> int:
        raise Exception("Not implemented yet")

    @allure.step("Checking if file {file_name} exist")
    def is_path_exist(self, path: str) -> bool:
        raise Exception("Not implemented yet")

    @allure.step("Create new folder {folder_path}")
    def create_new_folder(self, folder_path: str):
        raise Exception("Not implemented yet")

    def mount_shared_drive_locally(self, desired_local_drive: str, shared_drive: str, user_name: str, password: str):
        raise Exception("Not implemented yet")

    def remove_all_mounted_drives(self):
        raise Exception("Not implemented yet")

    def copy_files(self, source: str, target: str):
        raise Exception("Not implemented yet")

    @allure.step("Removing file {file_path}")
    def remove_file(self, file_path):
        cmd = f"rm -f {file_path}"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    def overwrite_file_content(self, content: str, file_path: str):
        raise Exception("Not implemented yet")
