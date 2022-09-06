from datetime import datetime
from typing import List

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.containers.system_component_containers import CoreDetails
from infra.enums import ComponentType
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation


class Core(FortiEdrLinuxStation):

    def __init__(self,
                 host_ip: str,
                 core_details: CoreDetails | None,
                 ssh_user_name: str = 'root',
                 ssh_password: str = 'enSilo$$'):
        super().__init__(host_ip=host_ip,
                         user_name=ssh_user_name,
                         password=ssh_password,
                         component_type=ComponentType.CORE)
        self._details = core_details
        self.__parsed_logs_location = "/tmp/parsed_logs"
        self.__is_blg_parser_exist_for_current_version = True

    def __repr__(self):
        return f"Core {self._host_ip}"

    @property
    def details(self) -> CoreDetails:
        return self._details

    @details.setter
    def details(self, details: CoreDetails):
        self._details = details

    def get_logs_folder_path(self):
        return "/opt/FortiEDR/core/Logs/Core"

    def _is_dedicated_blg_log_parser_exist_for_version(self, version):
        log_parser_name = f'blg2log_{version}'
        parser_full_path = f'{self._version_content_folder}/{log_parser_name}'
        is_parser_exist_on_machine = self.is_path_exist(path=parser_full_path)
        if not is_parser_exist_on_machine:
            copied_files_dir = self.copy_files_from_shared_versions_folder(version=version,
                                                                           files_names=[log_parser_name])
            files_paths = self.get_list_of_files_in_folder(copied_files_dir)
            if parser_full_path in files_paths:
                return True

            return False

        return True

    @allure.step("{0} - Clear logs")
    def clear_logs(self,
                   file_suffix='.blg'):
        """
        This method role is to clear all log files except the last modified file.

        :param file_suffix: consider only files with .blg suffix
        :return: None
        """

        # better to stop service since we don't know what will happen if we remove file during service writing to it.
        self.stop_service()
        log_folder = self.get_logs_folder_path()
        Reporter.report("Going to remove all core .blg log files")
        self.remove_file(file_path=f'{log_folder}/*.*')
        self.start_service()

    @allure.step("{0} - Append logs to report")
    def append_logs_to_report(self, file_suffix='.blg'):
        """
        This method is used to append logs to report
        it will parse ALL .blg logs that found under /opt/FortiEDR/core/Logs/Core and attach it to allure report
        :param file_suffix: log files to parse with the given suffix
        """
        if file_suffix != '.blg':
            file_suffix = '.blg'

        log_folder = self.get_logs_folder_path()

        blg_log_files = self.get_list_of_files_in_folder(log_folder, file_suffix=file_suffix)

        parsed_log_paths = self.get_parsed_blg_log_files(blg_log_files_paths=blg_log_files)

        for single_file in parsed_log_paths:
            content = self.get_file_content(file_path=single_file)

            if content is None:
                Reporter.report(f"There is no new logs in file: {single_file} - nothing to attach")

            Reporter.attach_str_as_file(file_name=single_file, file_content=content)

    def _get_log_files_ready_for_append(self,
                                        first_log_timestamp,
                                        machine_datetime_format="%d/%m/%Y %H:%M:%S"):
        log_folder = self.get_logs_folder_path()
        blg_log_files = self.get_list_of_files_in_folder(log_folder, file_suffix='.blg')

        # parse only files that was last modified after the first_log_timestamp
        parsed_log_paths = self.get_parsed_blg_log_files(blg_log_files_paths=blg_log_files,
                                                         modified_after_date_time=first_log_timestamp,
                                                         machine_datetime_format=machine_datetime_format)
        return parsed_log_paths

    @allure.step("{0} - Get parsed log files")
    def get_parsed_blg_log_files(self,
                                 blg_log_files_paths: List[str],
                                 default_blg_version_parser: str = '5.0.10.202',
                                 modified_after_date_time=None,
                                 machine_datetime_format="%d/%m/%Y %H:%M:%S"):

        version = self.get_version()

        # will try to copy blg2log for current version only 1 time, if there is no such file in shared folder
        # we won't try to copy it again
        is_fallback_parser_exist_for_current_version = False
        if self.__is_blg_parser_exist_for_current_version is True:
            try:
                self.__is_blg_parser_exist_for_current_version = self._is_dedicated_blg_log_parser_exist_for_version(version=version)
            except Exception as e: # workaround for case that there is blg2log file for current version in shared folder
                self.__is_blg_parser_exist_for_current_version = False

        # note that it can not be else to the if above since we need to know the result of the methord inside the if.
        if self.__is_blg_parser_exist_for_current_version is False:
            is_fallback_parser_exist_for_current_version = self._is_dedicated_blg_log_parser_exist_for_version(version=default_blg_version_parser)

            if is_fallback_parser_exist_for_current_version is False:
                raise Exception("Can not parse since there is no blg2log for log parsing")

        log_parser_name = f'blg2log_{version}'
        if self.__is_blg_parser_exist_for_current_version:
            log_parser_name = f'blg2log_{version}'

        elif not self.__is_blg_parser_exist_for_current_version and is_fallback_parser_exist_for_current_version:
            log_parser_name = f'blg2log_{default_blg_version_parser}'

        else:
            assert False, "Can not parse .blg logs file of Core since there is no blg2log parser on machine"

        parser_full_path = f'{self._version_content_folder}/{log_parser_name}'

        # parse logs
        converted_files_paths = []

        with allure.step(f"Filter log files that was created after: {modified_after_date_time}"):
            for blg_log_file_path in blg_log_files_paths:

                if modified_after_date_time is not None:

                    # check if file modified after initial timestamp
                    current_file_modified_date = self.get_file_last_modify_date(file_path=blg_log_file_path, date_format=machine_datetime_format)

                    first_timestamp_date_time = datetime.strptime(modified_after_date_time, machine_datetime_format)
                    current_file_modified_date_time = datetime.strptime(current_file_modified_date, machine_datetime_format)

                    if current_file_modified_date_time < first_timestamp_date_time:
                        continue

                cmd = f"{parser_full_path} -q {blg_log_file_path}"
                output = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False, attach_output_to_report=True)
                if f'converting {blg_log_file_path}' not in output:
                    assert False, "Failed to parse log file"

                # check that .log file is exist
                converted_file = blg_log_file_path.replace('.blg', '.log')
                Reporter.report(f"Checking that {converted_file} created")
                is_parsed_log_files_created = self.is_path_exist(path=converted_file)
                if not is_parsed_log_files_created:
                    assert False, "Parsed log file are not created, check if .blg file to be parsed"

                # read file content
                converted_files_paths.append(blg_log_file_path.replace('.blg', '.log'))

        return converted_files_paths
