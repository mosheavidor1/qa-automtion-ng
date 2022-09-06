import re
from datetime import datetime
from typing import List
from infra.enums import LinuxDistroTypes

import allure
import paramiko
import third_party_details
from infra.allure_report_handler.reporter import Reporter, INFO
from infra.decorators import retry
from infra.os_stations.os_station_base import OsStation
from infra.utils.utils import StringUtils
from infra.common_utils import wait_for_condition
from .linux_distros import LinuxDistroDetails
import logging
logger = logging.getLogger(__name__)

INTERVAL_STATION_KEEPALIVE = 5
WAIT_FOR_STATION_UP_TIMEOUT = 4 * 60
WAIT_FOR_STATION_DOWN_TIMEOUT = 2 * 60
COLLECTOR_TEMP_PATH = "/tmp"
COLLECTOR_EDR_EVENT_TESTER_PATH = f"{COLLECTOR_TEMP_PATH}/edr_event_tester"


class LinuxStation(OsStation):

    def __init__(self, host_ip: str, user_name: str, password: str):
        OsStation.__init__(self, host_ip=host_ip, user_name=user_name, password=password)
        self.distro_type = self.get_distro_type()
        self.distro_data = LinuxDistroDetails(self.distro_type)
        self.__collector_installation_path: str = ""
        self.__collector_config_folder: str = ""

        self.__qa_files_path: str = COLLECTOR_TEMP_PATH

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
        self._remote_connection_session = None

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
            self.establish_ssh_active_session()
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
                    logger.info(f"Failing because stderr was returned, error is: {stderr_err_output}")
                    assert False, f"Failing because stderr was returned, error is: {stderr_err_output}"

                if return_output:
                    return output

        except Exception as e:
            Reporter.report(f'Failed to execute command {cmd} on remote Linux machine, original exception: {e}')
            self.disconnect()
            raise e

    def establish_ssh_active_session(self):
        ssh_client = self._remote_connection_session
        if ssh_client is not None:
            if not ssh_client.get_transport().is_active():
                self.disconnect()
                self.connect()
        elif ssh_client is None:
            self.connect()

    def get_os_architecture(self):
        cmd = 'arch'
        result = self.execute_cmd(cmd=cmd, return_output=True)
        return result

    def get_hostname(self):
        raise Exception("Not Implemented yet")

    def get_installed_package_name(self, program_name):
        """ Return the desired program name as installed in the linux distro """
        cmd = f"{self.distro_data.commands.installed_packages} | grep -i {program_name}"
        package_installed_name = self.execute_cmd(cmd=cmd)
        return package_installed_name

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

    @allure.step("Reboot collector")
    def reboot(self):
        ip_before_reboot = self.vm_operations.vm_obj.guest.ipAddress
        logger.info(f"ip before reboot is: {ip_before_reboot}")
        uptime_sec_before_reboot = self.get_machine_uptime_seconds()
        cmd = 'reboot'
        self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        self.wait_until_machine_is_unreachable()
        try:
            self.wait_until_machine_is_reachable()
        except Exception as e:
            logger.info("Machine is not reachable, After reboot a new ip might be assigned to the vm")
            current_ip = self.vm_operations.vm_obj.guest.ipAddress
            logger.info(f"ip after reboot is: {current_ip}")
            if current_ip == ip_before_reboot:
                logger.info("The ip was not changed so machine is unreachable because a real issue")
                raise e
            else:
                logger.info(f"Update the ip to: {current_ip} and validate machine is reachable with the new ip")
                self.host_ip = current_ip
                self.wait_until_machine_is_reachable()

        uptime_sec_after_reboot = self.get_machine_uptime_seconds()
        assert uptime_sec_after_reboot < uptime_sec_before_reboot, "Machine was not actually rebooted"

    @allure.step("Get current linux machine uptime in seconds")
    def get_machine_uptime_seconds(self):
        cmd = "awk '{print $1}' /proc/uptime"
        uptime_sec = self.execute_cmd(cmd=cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        Reporter.report(f"Uptime sec is {uptime_sec}")
        return int(float(uptime_sec))

    def is_reachable(self):
        try:
            self._remote_connection_session = paramiko.SSHClient()
            self._remote_connection_session.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
            self._remote_connection_session.connect(hostname=self.host_ip, username=self.user_name,
                                                    password=self.password)
            return True
        except:
            return False

    @allure.step("Wait until machine is unreachable")
    def wait_until_machine_is_unreachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_DOWN_TIMEOUT

        def predict():
            result = not self.is_reachable()
            return result

        wait_for_condition(condition_func=predict, timeout_sec=timeout,
                           interval_sec=INTERVAL_STATION_KEEPALIVE, condition_msg="VM is unreachable")

    @allure.step("Wait until machine is reachable")
    def wait_until_machine_is_reachable(self, timeout=None):
        timeout = timeout or WAIT_FOR_STATION_UP_TIMEOUT
        predict_condition_func = self.is_reachable
        wait_for_condition(condition_func=predict_condition_func, timeout_sec=timeout,
                           interval_sec=INTERVAL_STATION_KEEPALIVE, condition_msg="VM is reachable")

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
    def get_file_content(self, file_path, filter_regex: str = None):
        cmd = f"cat {file_path}"
        if filter_regex is not None:
            cmd = f'grep -E "{filter_regex}" {file_path}'
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

    @allure.step("Get files inside {folder_path} include file size and datetime")
    def get_files_details(self, folder_path: str) -> List[dict]:
        raise NotImplemented("Should be implemented")

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

    @allure.step("Get malware {malware_name} process ID")
    def get_malware_process_id(self, malware_name: str) -> int:
        cmd = f"ps aux | grep -w '{malware_name}' | grep -v grep | awk '{{print $2}}'"
        pid = self.execute_cmd(cmd=cmd)
        if pid is None:
            return None
        pid = int(pid)
        return pid

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
        cmd = f"sudo umount --force {local_mounted_drive}"
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)
        mounted_files_paths = self.get_list_of_files_in_folder(folder_path=local_mounted_drive)
        assert mounted_files_paths is None, \
            f"Failed to unmount {local_mounted_drive}, still contains these files: {mounted_files_paths}"

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

    @allure.step("Overwrite {file_path} content")
    def overwrite_file_content(self, content: str, file_path: str):
        cmd = f'echo "{content}" > {file_path}'
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("append text to file {file_path}")
    def append_text_to_file(self, content: str, file_path: str):
        cmd = f'echo "" >> {file_path} && echo "{content}" >> {file_path}'
        self.execute_cmd(cmd=cmd, return_output=False, fail_on_err=True)

    @allure.step("Copy files from shared folder to local machine")
    @retry
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
        assert len(files_to_copy) > 0, "Must pass the names of the files"
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
            mounted_successfully = True
            files_in_mounting_point = self.get_list_of_files_in_folder(folder_path=mounted_dir_name)
            for file_name_to_copy in files_to_copy:
                mounted_file_path_to_copy = f'{mounted_dir_name}/{file_name_to_copy}'
                if file_name_to_copy != '*':
                    assert mounted_file_path_to_copy in files_in_mounting_point, \
                        f"'{file_name_to_copy}' does not exist in mounting point '{mounted_dir_name}'"
                self.copy_files(source=mounted_file_path_to_copy, target=target_folder)
                if file_name_to_copy != '*':
                    copied_file_path = f'{target_folder}/{file_name_to_copy}'
                    assert copied_file_path in self.get_list_of_files_in_folder(folder_path=target_folder), \
                        f"'{file_name_to_copy}' was not copied to '{target_folder}'"
            return target_folder

        finally:
            if mounted_successfully:
                self.remove_mounted_drive(local_mounted_drive=mounted_dir_name)
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

    def get_distro_type(self):
        os_name = self.os_name.lower()
        if "ubuntu" in os_name:
            return LinuxDistroTypes.UBUNTU
        elif "centos" in os_name:
            return LinuxDistroTypes.CENTOS

    @allure.step("Extract compressed file")
    def extract_compressed_file(self, file_path_to_extract=None, file_name=None):
        """
        This functions extracts the provided file_path to provided output_path.
        """
        output_path = COLLECTOR_EDR_EVENT_TESTER_PATH

        cmd = f'unzip {COLLECTOR_EDR_EVENT_TESTER_PATH}/{file_name} -d {output_path}'

        output = self.execute_cmd(f"{cmd}")
        Reporter.report(f"Extraction output\n {output}", INFO)

        return output_path

    def wait_for_file_to_appear_in_specified_folder(self, file_path: str, file_name: str, timeout: int, interval: int):
        raise NotImplementedError()

    @allure.step("Check if {path} is file")
    def is_file(self, path: str) -> bool:
        raise Exception("Not Implemented yet")

    @allure.step("Check if {path} is folder")
    def is_folder(self, path: str) -> bool:
        raise Exception("Not Implemented yet")
