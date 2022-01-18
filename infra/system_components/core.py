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

    @allure.step("Get parsed log file")
    def get_parsed_blg_log_file_path(self, blg_log_file_path: str):

        if '.blg' not in blg_log_file_path:
            raise ValueError("Can not parse file with suffix different than .blg")

        version = self.get_version()
        log_parser_name = f'blg2log_{version}'

        parser_full_path = f'{self._version_content_folder}/{log_parser_name}'
        is_parser_exist_in_local_machine = self.is_path_exist(path=parser_full_path)

        if not is_parser_exist_in_local_machine:
            copied_files_dir = self.copy_version_files_from_shared_folder()
            Reporter.report("Checking if parser exist after copy content of versions files from shared folder")
            is_parser_exist_in_local_machine = self.is_path_exist(path=f'{copied_files_dir}/{log_parser_name}')
            if not is_parser_exist_in_local_machine:
                assert False, f"Can not find {log_parser_name} under {copied_files_dir} so can not parse the blg log files"

        # parse logs
        cmd = f"{parser_full_path} -q {blg_log_file_path}"
        output = self.execute_cmd(cmd=cmd, return_output=True, fail_on_err=False)
        if output != f'converting {blg_log_file_path}':
            assert False, "Failed to parse log file"

        # check that .log file is exist
        converted_file = blg_log_file_path.replace('.blg', '.log')
        Reporter.report(f"Checking that {converted_file} created")
        is_parsed_log_files_created = self.is_path_exist(path=converted_file)
        if not is_parsed_log_files_created:
            assert False, "Parsed log file are not created, check if .blg file to be parsed"

        # read file content
        converted_file_path = blg_log_file_path.replace('.blg', '.log')
        return converted_file_path



