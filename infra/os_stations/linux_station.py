import re
from datetime import datetime
from typing import List

import allure
import paramiko

import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.decorators import retry
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

    @retry
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

    @retry
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
                    if output is not None and len(output) > 1000:

                        if len(output) < 2000000:
                            Reporter.attach_str_as_file(file_name='command output', file_content=output)
                        else:
                            Reporter.report("Content is to big to attach to allure report, sorry")

                    else:
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

    def get_hostname(self):
        raise Exception("Not Implemented yet")

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

    def stop_service(self, service_name: str):
        raise Exception("Not Implemented yet")

    def start_service(self, service_name: str):
        raise Exception("Not Implemented yet")

    @allure.step("Reboot")
    def reboot(self):
        raise Exception("Not Implemented yet")

    @allure.step("Get current linux machine date time")
    def get_current_machine_datetime(self, date_format="%d/%m/%Y %H:%M:%S"):
        cmd = f"date '+{date_format}'"
        result = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=True, attach_output_to_report=True)
        return result

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
    def get_file_content_within_range(self, file_path, start_index, end_index=None):

        cmd = f"sed -n '{str(start_index)},$p' {file_path}"

        if end_index is not None:

            if start_index == end_index or start_index > end_index:
                return ""

            cmd = f"sed -n '{str(start_index)},{str(end_index)}p; {str(end_index+1)}q' {file_path}"

        output = self.execute_cmd(cmd=cmd)
        return output

    @allure.step("Get Line numbers that matching to pattern")
    def get_line_numbers_matching_to_pattern(self, file_path, pattern):
        cmd = f'cat {file_path} | grep -nE "{pattern}" | cut -d : -f 1'
        output = self.execute_cmd(cmd=cmd)
        if output is None:
            return None
        lines = output.split('\n')
        return lines

    @allure.step("Get list of files paths inside {folder_path} with the suffix {file_suffix}")
    def get_list_of_files_in_folder(self, folder_path: str, file_suffix: str = None):
        result = self.execute_cmd(f'ls {folder_path}')
        if result is None:
            return result
        files_names = result.split('\n')
        if file_suffix is not None:
            files_names = [file_name for file_name in files_names if file_suffix in file_name]
        files_paths = [f'{folder_path}/{file_name}' for file_name in files_names]
        return files_paths

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

    @allure.step("Get {service_identifier} service process ID")
    def get_service_process_ids(self, service_identifier: str) -> List[int]:
        # pid_of_fortiedr_scanner in old infra
        cmd = f"ps aux | grep '{service_identifier}' | grep -v grep | awk '{{print $2}}'"
        pid = self.execute_cmd(cmd=cmd)
        if pid is None:
            return None
        pids = [int(pid)]
        return pids

    @allure.step("Kill process with the id: {pid}")
    def kill_process_by_id(self, pid):
        raise Exception("Not implemented yet")

    @allure.step("Checking if {path} exist")
    def is_path_exist(self, path: str) -> bool:
        expected_message = "exist"

        # check if dir exist
        cmd = f'[ -d {path} ] && echo "{expected_message}"'
        result_dir = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)

        # check if file exist
        cmd = f'[ -f {path} ] && echo "{expected_message}"'
        result_file = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)

        if (result_dir is not None and expected_message in result_dir) or (result_file is not None and expected_message in result_file):
            Reporter.report(f"Path {path} exist!")
            return True

        Reporter.report(f"Path {path} is not exist")
        return False

    @allure.step("Create new folder {folder_path}")
    def create_new_folder(self, folder_path: str):
        if self.is_path_exist(path=folder_path):
            return folder_path

        create_new_folder_command = f"mkdir -p {folder_path}"
        self.execute_cmd(cmd=create_new_folder_command, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return folder_path

    @allure.step("Mount shared drive locally")
    def mount_shared_drive_locally(self, desired_local_drive: str, shared_drive: str, user_name: str, password: str):
        cmd = f"sudo mount -t cifs -o username={user_name},password={password} {shared_drive} {desired_local_drive}"
        self.execute_cmd(cmd=cmd, fail_on_err=True)

    @allure.step("Unmount shared drive {local_mounted_drive}")
    def remove_mounted_drive(self, local_mounted_drive: str = None):
        cmd = f"sudo sudo umount --force {local_mounted_drive}"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    def copy_files(self, source: str, target: str):
        cmd = f'scp -r {source} {target}'
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Removing file {file_path}")
    def remove_file(self, file_path):
        cmd = f"rm -f {file_path}"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Removing folder {folder_path}")
    def remove_folder(self, folder_path: str):
        cmd = f"rm -rf {folder_path}"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    def overwrite_file_content(self, content: str, file_path: str):
        raise Exception("Not implemented yet")

    @allure.step("Copy files from shared folder to local machine")
    def copy_files_from_shared_folder(self,
                                      target_path_in_local_machine: str,
                                      shared_drive_path: str,
                                      shared_drive_user_name: str,
                                      shared_drive_password: str,
                                      files_to_copy: List[str]):
        """
        The role of this method is to copy files from the shared folder to target folder in the remote station
        :param target_path_in_local_machine: target folder for copied files
        :param shared_drive_path: path in shared drive folder, must be a path to folder
        :param shared_drive_user_name: user name
        :param shared_drive_password: password
        :param files_to_copy: list of file names to copy, if you want to copy all files in folder, pass ['*']
        :return: folder path of the copied files
        """

        curr_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        mounted_dir_name = f'/mnt/{curr_time}'
        mounted_successfully = False
        try:
            target_folder = self.create_new_folder(folder_path=target_path_in_local_machine)
            mounted_dir_name = self.create_new_folder(folder_path=mounted_dir_name)
            shared_drive_ip = self.get_ip_of_remote_host(host=third_party_details.SHARED_DRIVE_PATH.replace('\\', ''))
            shared_drive_path_for_command = shared_drive_path.replace("\\", "/")
            str_to_replace = third_party_details.SHARED_DRIVE_PATH.replace('\\', '')
            shared_drive_path_for_command = shared_drive_path_for_command.replace(str_to_replace, shared_drive_ip)

            self.mount_shared_drive_locally(desired_local_drive=mounted_dir_name,
                                            shared_drive=shared_drive_path_for_command,
                                            user_name=shared_drive_user_name,
                                            password=shared_drive_password)

            for single_file in files_to_copy:
                self.copy_files(source=f'{mounted_dir_name}/{single_file}', target=target_folder)

            return target_folder

        finally:
            # unmount
            if mounted_successfully is True:
                self.remove_mounted_drive(local_mounted_drive=mounted_dir_name)
                # remove file
                self.remove_folder(mounted_dir_name)

    def get_last_modified_file_name_in_folder(self, folder_path: str, file_suffix: str = None) -> str:
        cmd = f'ls -t {folder_path}'
        output = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=True)
        if output is None:
            return None

        files = output.split('\n')
        if len(files) == 0:
            return None

        if file_suffix is not None:
            for i in range(len(files)):
                if file_suffix in files[i]:
                    return files[i]

        return files[0]

    def move_file(self, file_name: str, target_folder: str):
        raise Exception("There is no implementation yet")

    @allure.step("Get file last modify date")
    def get_file_last_modify_date(self, file_path: str, date_format: str="%d/%m/%Y %H:%M:%S") -> str:
        cmd = f'date -r {file_path} +"{date_format}"'
        output = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=True)
        return output
