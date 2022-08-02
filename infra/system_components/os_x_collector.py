import allure
from infra.enums import OsTypeEnum
from infra.system_components.collector import CollectorAgent


class OsXCollector(CollectorAgent):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password,
                         os_type=OsTypeEnum.OS_X)
        self._process_id = self.get_current_process_id()

    @property
    def cached_process_id(self) -> int:
        return self._process_id

    def update_process_id(self):
        pass

    @allure.step("Get current collector process ID")
    def get_current_process_id(self):
        pass

    def get_version(self):
        pass


    def reboot(self):
        pass

    def stop_collector(self, password: str):
        pass

    def start_collector(self):
        pass

    def has_crash(self):
        pass

    def has_crash_dumps(self, append_to_report: bool):
        pass

    def copy_version_files_to_local_machine(self, version: str):
        pass

    def get_agent_status(self):
        pass

    def is_agent_running(self):
        pass

    def install_collector(self, version: str, aggregator_ip: str, organization: str = None, aggregator_port: int = 8081,
                          registration_password: str = '12345678', append_log_to_report=True):
        pass

    def uninstall_collector(self, registration_password: str = '12345678', append_log_to_report=True):
        pass

    def get_logs_content(self, file_suffix='.blg', filter_regex=None):
        pass

    def append_logs_to_report(self, first_log_timestamp_to_append: str = None, file_suffix='.blg'):
        pass

    def clear_logs(self):
        pass

    def copy_log_parser_to_machine(self):
        pass

    def remove_all_crash_dumps_files(self):
        pass
