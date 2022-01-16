import ipaddress
from abc import ABCMeta, abstractmethod
from typing import List

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.utils.utils import StringUtils


class OsStation(metaclass=ABCMeta):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str):
        self._host_ip = host_ip
        self._user_name = user_name
        self._password = password
        self._remote_connection_session = None
        self._os_architecture = None
        self._os_version = None
        self._os_name = None

        self._init_os_details()

    @property
    def host_ip(self) -> str:
        return self._host_ip

    @host_ip.setter
    def host_ip(self, host_ip: str):
        try:
            ipaddress.ip_address(host_ip)
            self._host_ip = host_ip
        except Exception as e:
            raise Exception("Please insert valid Host IP")

    @property
    def user_name(self) -> str:
        return self._user_name

    @user_name.setter
    def user_name(self, user_name: str):
        self._user_name = user_name

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str):
        self._password = password

    @property
    def os_architecture(self):
        return self._os_architecture

    @property
    def os_name(self):
        return self._os_name

    @property
    def os_version(self):
        return self._os_version

    def _init_os_details(self):
        self._os_version = self.get_os_version()
        self._os_name = self.get_os_name()
        self._os_architecture = self.get_os_architecture()

    @allure.step("Get IP of a remote host {host}")
    def get_ip_of_remote_host(self, host):
        cmd = f"ping -c 1 {host}"
        result = self.execute_cmd(cmd=cmd,
                                  return_output=True,
                                  fail_on_err=False,
                                  attach_output_to_report=True,
                                  asynchronous=False)
        if 'unreachable' in result.lower():
            Reporter.report("host is unreachable, can't get IP")
            return None

        ip = StringUtils.get_txt_by_regex(text=result, regex='(\d+\.\d+.\d+.\d+)', group=1)
        Reporter.report(f"The Ip is: {ip}")
        return ip

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def execute_cmd(self, cmd: str, return_output: bool = True, fail_on_err: bool = False, timeout: int = 180,
                    attach_output_to_report: bool = True,
                    asynchronous: bool = False):
        pass

    @abstractmethod
    def get_os_architecture(self):
        pass

    @abstractmethod
    def get_os_version(self):
        pass

    @abstractmethod
    def get_os_name(self):
        pass

    @abstractmethod
    def get_cpu_usage(self):
        pass

    @abstractmethod
    def get_memory_usage(self):
        pass

    @abstractmethod
    def get_disk_usage(self):
        pass

    @abstractmethod
    def get_process_id(self, service_name: str) -> int:
        pass

    @abstractmethod
    def is_path_exist(self, path: str) -> bool:
        pass

    @abstractmethod
    def get_file_content(self, file_path: str) -> str:
        pass

    @abstractmethod
    def create_new_folder(self, folder_path: str) -> str:
        pass

    @abstractmethod
    def remove_mounted_drive(self, local_mounted_drive: str = None):
        pass

    @abstractmethod
    def mount_shared_drive_locally(self,
                                   desired_local_drive: str,
                                   shared_drive: str,
                                   user_name: str,
                                   password: str):
        pass

    @abstractmethod
    def copy_files_from_shared_folder_to_local_machine(self,
                                                       target_path_in_local_machine: str,
                                                       shared_drive_path: str,
                                                       shared_drive_user_name: str,
                                                       shared_drive_password: str):
        pass

    @abstractmethod
    def copy_files(self, source: str, target: str):
        pass

    @abstractmethod
    def remove_file(self, file_path: str):
        pass

    @abstractmethod
    def remove_folder(self, folder_path: str):
        pass

    @abstractmethod
    def get_list_of_files_in_folder(self,
                                    folder_path: str,
                                    file_suffix: str = None) -> List[str]:
        pass

    @abstractmethod
    def overwrite_file_content(self, content: str, file_path: str):
        pass
