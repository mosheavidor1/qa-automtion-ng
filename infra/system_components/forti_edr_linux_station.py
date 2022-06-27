import time
from abc import abstractmethod
from datetime import datetime
from typing import List

import allure

import third_party_details
from infra.forti_edr_versions_service_handler.forti_edr_versions_service_handler import FortiEdrVersionsServiceHandler
from infra.allure_report_handler.reporter import Reporter
from infra.enums import FortiEdrSystemState, ComponentType
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

    def __repr__(self):
        return f"{self.__component_type.name} {self._host_ip}"

    @property
    def component_type(self) -> ComponentType:
        return self.__component_type

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
        Reporter.report(f"Get status of {self.__component_type.value}")
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

    @allure.step("{0} restart service")
    def restart_service(self):
        cli_cmd = f'fortiedr {self.__component_type.value} restart'
        result = self.execute_cmd(cmd=cli_cmd, fail_on_err=True)
        if result is not None and "OK" in result:
            return result
        else:
            raise Exception(f"Unable to restart the '{self.__component_type.value}' service")

    @allure.step('Validate {0} service state is "{desired_state}"')
    def validate_system_component_is_in_desired_state(self,
                                                      desired_state: FortiEdrSystemState):

        assert self.is_system_in_desired_state(desired_state), f"service is not {desired_state.name}"

    def is_system_in_desired_state(self, desired_state: FortiEdrSystemState):
        status = self.get_status()

        expected_running_cmd = f'[+] {self.__component_type.value} is running'
        expected_not_running_cmd = f'[-] {self.__component_type.value} is not running'

        if self.__component_type == ComponentType.MANAGEMENT:
            expected_running_cmd = expected_running_cmd.replace(self.__component_type.value, 'webapp')
            expected_not_running_cmd = expected_not_running_cmd.replace(self.__component_type.value, 'webapp')

        if desired_state == FortiEdrSystemState.RUNNING and expected_running_cmd in status:
            Reporter.report(f"service is up and running as expected")
            return True

        elif desired_state == FortiEdrSystemState.NOT_RUNNING and expected_not_running_cmd in status:
            Reporter.report(f"service is not up and running as expected")
            return True

        else:
            Reporter.report(f"the status is {status}, not as expected")
            return False

    @allure.step('Wait until service will be in desired state: {desired_state}')
    def wait_until_service_will_be_in_desired_state(self,
                                                    desired_state: FortiEdrSystemState,
                                                    timeout: int = 5*60,
                                                    check_interval: int = 10):
        start_time = time.time()
        is_system_in_desired_state = self.is_system_in_desired_state(desired_state=desired_state)
        while time.time() - start_time < timeout and not is_system_in_desired_state:
            Reporter.report(f'going to sleep {check_interval} seconds')
            time.sleep(check_interval)
            is_system_in_desired_state = self.is_system_in_desired_state(desired_state=desired_state)

        assert is_system_in_desired_state, f"{self.__component_type} is not in the state: {desired_state} within {timeout}"

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
    def copy_files_from_shared_versions_folder(self, version: str = None, files_names=None) -> List[str]:
        files_names = files_names or ['*']
        assert len(files_names) > 0, "Should pass the names of desired files"
        if version is None:
            version = self.get_version()

        shared_drive_path = fr'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'
        copied_files_dir = self.copy_files_from_shared_folder(
            target_path_in_local_machine=self._version_content_folder, shared_drive_path=shared_drive_path,
            shared_drive_user_name=third_party_details.USER_NAME, shared_drive_password=third_party_details.PASSWORD,
            files_to_copy=files_names)

        return copied_files_dir

    def _get_first_log_row_that_macthing_to_date_regex(self,
                                                       file_path,
                                                       log_file_datetime_regex_linux,
                                                       log_file_datetime_regex_python) -> str:
        first_row_log_with_date = self.execute_cmd(f"egrep '{log_file_datetime_regex_linux}' {file_path} | head -n 1")
        first_date_only = StringUtils.get_txt_by_regex(text=first_row_log_with_date, regex=f'({log_file_datetime_regex_python})', group=1)
        return first_date_only

    @allure.step("Checking if log file created after the given timestamp {given_timestamp}")
    def _is_log_file_created_after_given_timestamp(self,
                                                   log_file_path,
                                                   given_timestamp,
                                                   log_datetime_format,
                                                   log_file_datetime_regex_linux: str,
                                                   log_file_datetime_regex_python: str) -> bool:
        first_timestamp_in_log = self._get_first_log_row_that_macthing_to_date_regex(file_path=log_file_path,
                                                                                     log_file_datetime_regex_linux=log_file_datetime_regex_linux,
                                                                                     log_file_datetime_regex_python=log_file_datetime_regex_python)

        first_time_stamp_datetime = datetime.strptime(first_timestamp_in_log, log_datetime_format)
        given_time_stamp_datetime = datetime.strptime(given_timestamp, log_datetime_format)

        if first_time_stamp_datetime >= given_time_stamp_datetime:
            Reporter.report(f"Log file was created after given time stamp: {given_timestamp}")
            return True

        Reporter.report(f"Log file was not created after given time stamp: {given_timestamp}")
        return False

    def _get_log_files_ready_for_append(self,
                                        first_log_timestamp,
                                        machine_datetime_format):
        log_folder = self.get_logs_folder_path()
        log_files = self.get_list_of_files_in_folder(folder_path=log_folder, file_suffix='.log')

        relevant_log_files = []
        with allure.step(f"Filter log files that was created after: {first_log_timestamp}"):
            for file in log_files:
                current_file_modified_date = self.get_file_last_modify_date(file_path=file,
                                                                            date_format=machine_datetime_format)

                first_timestamp_date_time = datetime.strptime(first_log_timestamp, machine_datetime_format)
                current_file_modified_date_time = datetime.strptime(current_file_modified_date, machine_datetime_format)
                if current_file_modified_date_time > first_timestamp_date_time:
                    relevant_log_files.append(file)

        return relevant_log_files

    @allure.step("{0} - Append logs to report from a given log timestamp {first_log_timestamp}")
    def append_logs_to_report_by_given_timestamp(self,
                                                 first_log_timestamp: str,
                                                 machine_timestamp_date_format: str,
                                                 log_timestamp_date_format: str,
                                                 log_timestamp_date_format_regex_linux: str,
                                                 log_file_datetime_regex_python: str):
        """
        This method will append logs to report from the given initial timestamp
        """

        # first_log_timestamp = "2022-02-27 08:48:00"
        first_log_timestamp_date_time = datetime.strptime(first_log_timestamp, machine_timestamp_date_format)

        all_log_files = self._get_log_files_ready_for_append(first_log_timestamp=first_log_timestamp,
                                                             machine_datetime_format=machine_timestamp_date_format)

        if all_log_files is None or all_log_files == []:
            Reporter.report(f"There is no logs that was created after {first_log_timestamp}")

        for single_file in all_log_files:

            content = None

            lines_with_matching_date = self.get_line_numbers_matching_to_pattern(file_path=single_file,
                                                                                 pattern=first_log_timestamp)
            if lines_with_matching_date is not None and len(lines_with_matching_date) > 0:
                # if start date exist in logs file (same second) -> get the data between the initial date till end
                first_matching_log_line = lines_with_matching_date[0]
                content = self.get_file_content_within_range(file_path=single_file, start_index=first_matching_log_line,
                                                             end_index=None)

            elif self._is_log_file_created_after_given_timestamp(log_file_path=single_file,
                                                                 given_timestamp=first_log_timestamp,
                                                                 log_datetime_format=log_timestamp_date_format,
                                                                 log_file_datetime_regex_python=log_file_datetime_regex_python,
                                                                 log_file_datetime_regex_linux=log_timestamp_date_format_regex_linux):
                # else if log file was created after the given time stamp
                # (searching for first row in log file that contains date and extract the date, then comparing it)
                # if created after - getting all file
                content = self.get_file_content(file_path=single_file)

            else:
                # else go trough the entire file in order to search logs rows that matching to our test time,
                # logs that created after the start time
                tmp_content = self.get_file_content(file_path=single_file)
                tmp_content_splitted = tmp_content.split('\n')
                for single_line in tmp_content_splitted:
                    line_date = StringUtils.get_txt_by_regex(text=single_line, regex=f'({log_file_datetime_regex_python})',
                                                             group=1)

                    if line_date is not None:
                        if datetime.strptime(line_date, log_timestamp_date_format) > first_log_timestamp_date_time:
                            first_index = tmp_content.index(line_date)
                            content = tmp_content[first_index:]
                            break

            if content is not None:
                Reporter.attach_str_as_file(file_name=single_file, file_content=content)

    @allure.step("Upgrade {0} machine to build: {desired_build}")
    def upgrade_to_specific_build(self,
                                  desired_build: int = None,
                                  create_snapshot_before_upgrade: bool = False):
        """
        The role of this method is to upgrade build of the system component
        :param desired_build: specific build number or None for latest build
        """
        current_version = self.get_version()
        base_version = StringUtils.get_txt_by_regex(text=current_version, regex="(\d+.\d+.\d+)", group=1)
        current_build = StringUtils.get_txt_by_regex(text=current_version, regex="\d+.\d+.\d+.(\d+)", group=1)

        if desired_build is None:
            latest_versions = FortiEdrVersionsServiceHandler.get_latest_versions(base_version=base_version)
            match self.__component_type:
                case ComponentType.MANAGEMENT:
                    desired_build = latest_versions.get('management')
                case ComponentType.AGGREGATOR:
                    desired_build = latest_versions.get('aggregator')
                case ComponentType.CORE:
                    desired_build = latest_versions.get('core')

            assert desired_build is not None, f"did not found versions that matching to the component {self.__component_type}"

            desired_build = StringUtils.get_txt_by_regex(text=desired_build, regex="\d+.\d+.\d+.(\d+)", group=1)

        if int(desired_build) > int(current_build):

            if create_snapshot_before_upgrade:
                self.vm_operations.remove_all_snapshots()
                self.vm_operations.snapshot_create(snapshot_name=f"Before_upgrade_{StringUtils.generate_random_string(length=3)}")

            upgrade_file_name = f'FortiEDRInstaller_{base_version}.{desired_build}.x'
            shared_drive_path = fr'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{base_version}.{desired_build}'
            copied_files_dir = self.copy_files_from_shared_folder(
                target_path_in_local_machine=self._version_content_folder, shared_drive_path=shared_drive_path,
                shared_drive_user_name=third_party_details.USER_NAME, shared_drive_password=third_party_details.PASSWORD,
                files_to_copy=[upgrade_file_name])

            with allure.step("Going to upgrade to machine"):
                result = self.execute_cmd(cmd=f'{copied_files_dir}/{upgrade_file_name}', timeout=15*60)
                Reporter.attach_str_as_file(file_name='upgrade output', file_content=result)
                if 'FortiEDR patch installation finished successfully' not in result:
                    assert False, "Something went wrong during the upgrade"

            self.wait_until_service_will_be_in_desired_state(desired_state=FortiEdrSystemState.RUNNING)

        else:
            Reporter.report(f"Skipping upgrade since the current version is >= desired version, current build: {current_build}, desired build: {desired_build}")








