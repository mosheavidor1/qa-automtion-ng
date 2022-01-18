from typing import List

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.containers.system_component_containers import CoreDetails
from infra.enums import ComponentType
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation


class Core(FortiEdrLinuxStation):

    def __init__(self,
                 host_ip: str,
                 core_details: CoreDetails,
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
            copied_files_dir = self.copy_version_files_from_shared_folder(version=version)
            files_in_dir = self.get_list_of_files_in_folder(copied_files_dir)
            if log_parser_name in files_in_dir:
                return True

            return False

        return True

    @allure.step("Get parsed log files")
    def parse_blg_log_files(self,
                            blg_log_files_paths: List[str],
                            default_blg_version_parser: str = '5.0.10.202'):

        version = self.get_version()

        # will try to copy blg2log for current version only 1 time, if there is no such file in shared folder
        # we won't try to copy it again
        if self.__is_blg_parser_exist_for_current_version is True:
            self.__is_blg_parser_exist_for_current_version = self._is_dedicated_blg_log_parser_exist_for_version(version=version)

        is_fallback_parser_exist_for_current_version = self._is_dedicated_blg_log_parser_exist_for_version(version=default_blg_version_parser)

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

        for blg_log_file_path in blg_log_files_paths:
            cmd = f"{parser_full_path} -q {blg_log_file_path}"
            output = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False, attach_output_to_report=True)
            if output != f'converting {blg_log_file_path}':
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



