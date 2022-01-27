from abc import abstractmethod

import allure

import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.enums import SystemState, ComponentType
from infra.os_stations.linux_station import LinuxStation
from infra.utils.utils import StringUtils


class FortiEdrLinuxStation(LinuxStation):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 component_type: ComponentType):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password)

        self.__component_type = component_type
        self._version_content_folder = "/tmp/version_files"

    @abstractmethod
    def get_logs_folder_path(self):
        pass

    @allure.step("Get {0} version")
    def get_version(self):
        cli_cmd = 'fortiedr version'
        result = self.execute_cmd(cmd=cli_cmd)
        return result

    @allure.step("Get {0} service status")
    def get_status(self):
        cli_cmd = f'fortiedr {self.__component_type.value} status'
        result = self.execute_cmd(cmd=cli_cmd)
        return result

    @allure.step('Validate {0} service state is "{desired_state}"')
    def validate_system_component_is_in_desired_state(self,
                                                      desired_state: SystemState):

        status = self.get_status()

        expected_running_cmd = f'[+] {self.__component_type.value} is running'
        expected_not_running_cmd = f'[-] {self.__component_type.value} is not running'

        if self.__component_type == ComponentType.MANAGEMENT:
            expected_running_cmd = expected_running_cmd.replace(self.__component_type.value, 'webapp')
            expected_not_running_cmd = expected_not_running_cmd.replace(self.__component_type.value, 'webapp')

        if desired_state == SystemState.RUNNING and expected_running_cmd in status:
            Reporter.report(f"service is up and running as expected")

        elif desired_state == SystemState.NOT_RUNNING and expected_not_running_cmd in status:
            Reporter.report(f"service is not up and running as expected")

        else:
            assert False, f"service is not in the desired state, desired state: {desired_state.name}, actual: {status}"

    @allure.step("Clear {0} logs")
    def clear_logs(self, file_suffix='.log'):
        log_folder = self.get_logs_folder_path()
        files = self.get_list_of_files_in_folder(folder_path=log_folder,
                                                 file_suffix=file_suffix)

        for single_file in files:

            if self.__component_type == ComponentType.AGGREGATOR or self.__component_type.MANAGEMENT:

                result = StringUtils.get_txt_by_regex(text=single_file, regex='.log.(\d+)', group=1)
                if result is not None:
                    self.remove_file(single_file)
                else:
                    self.clear_file_content(single_file)


    @allure.step("Append {0} logs to report")
    def append_logs_to_report(self, file_suffix='.log'):
        log_folder = self.get_logs_folder_path()
        files = self.get_list_of_files_in_folder(folder_path=log_folder,
                                                 file_suffix=file_suffix)

        for file in files:
            content = self.get_file_content(file_path=file)
            if content is None:
                Reporter.report(f"There is no new logs in file: {file} - nothing to attach")
                continue

            Reporter.attach_str_as_file(file_name=file, file_content=content)

    @allure.step("Copy version files from shared folder to {0}")
    def copy_version_files_from_shared_folder(self, version: str = None):

        if version is None:
            version = self.get_version()

        shared_drive_path = fr'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'
        copied_files_dir = self.copy_files_from_shared_folder(
            target_path_in_local_machine=self._version_content_folder, shared_drive_path=shared_drive_path,
            shared_drive_user_name=third_party_details.USER_NAME, shared_drive_password=third_party_details.PASSWORD,
            files_to_copy=['*'])

        return copied_files_dir
