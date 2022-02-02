from abc import abstractmethod
from datetime import datetime
from typing import List

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
        result = self.execute_cmd(cmd=cli_cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("Get {0} service status")
    def get_status(self):
        cli_cmd = f'fortiedr {self.__component_type.value} status'
        result = self.execute_cmd(cmd=cli_cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("{0} Stop service")
    def stop_service(self):
        cli_cmd = f'fortiedr {self.__component_type.value} stop'
        result = self.execute_cmd(cmd=cli_cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
        return result

    @allure.step("{0} start service")
    def start_service(self):
        cli_cmd = f'fortiedr {self.__component_type.value} start'
        result = self.execute_cmd(cmd=cli_cmd, fail_on_err=True, return_output=True, attach_output_to_report=True)
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
        """
        The role of this method is to remove all old log files
        determine old log file by suffix, for example if file name is xxxx.log.1, it will be removed
        :param file_suffix: consider only files with .log suffix
        :return: None
        """

        log_folder = self.get_logs_folder_path()
        files = self.get_list_of_files_in_folder(folder_path=log_folder,
                                                 file_suffix=file_suffix)

        for single_file in files:

            if self.__component_type == ComponentType.AGGREGATOR or self.__component_type.MANAGEMENT:

                result = StringUtils.get_txt_by_regex(text=single_file, regex=f'{file_suffix}.(\d+)', group=1)
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
    def copy_version_files_from_shared_folder(self, version: str = None) -> List[str]:

        if version is None:
            version = self.get_version()

        shared_drive_path = fr'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'
        copied_files_dir = self.copy_files_from_shared_folder(
            target_path_in_local_machine=self._version_content_folder, shared_drive_path=shared_drive_path,
            shared_drive_user_name=third_party_details.USER_NAME, shared_drive_password=third_party_details.PASSWORD,
            files_to_copy=['*'])

        return copied_files_dir

    def _get_first_log_row_that_macthing_to_date_regex(self, file_path, machine_timestamp_regex='(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+):(\d+)') -> str:
        first_row_log_with_date = self.execute_cmd(f"egrep '[0-9]{{2}}/[0-9]{{2}}/[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}' {file_path} | head -n 1")
        first_date_only = StringUtils.get_txt_by_regex(text=first_row_log_with_date, regex=f'({machine_timestamp_regex})', group=1)
        return first_date_only

    @allure.step("Checking if log file created after the given timestamp {given_timestamp}")
    def _is_log_file_created_after_given_timestamp(self, log_file_path, given_timestamp) -> bool:
        first_timestamp_in_log = self._get_first_log_row_that_macthing_to_date_regex(file_path=log_file_path)

        first_time_stamp_datetime = datetime.strptime(first_timestamp_in_log, "%d/%m/%Y %H:%M:%S")
        given_time_stamp_datetime = datetime.strptime(given_timestamp, "%d/%m/%Y %H:%M:%S")

        if first_time_stamp_datetime >= given_time_stamp_datetime:
            Reporter.report(f"Log file was created after given time stamp: {given_timestamp}")
            return True

        Reporter.report(f"Log file was not created after given time stamp: {given_timestamp}")
        return False






