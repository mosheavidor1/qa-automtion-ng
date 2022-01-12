from infra.containers.system_component_containers import CollectorDetails
from infra.enums import OsTypeEnum
from infra.system_components.collector import Collector


class OsXCollector(Collector):

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 collector_details: CollectorDetails):
        super().__init__(host_ip=host_ip,
                         user_name=user_name,
                         password=password,
                         collector_details=collector_details,
                         os_type=OsTypeEnum.OS_X)

    def _update_process_id(self):
        pass

    def get_service_name(self):
        pass

    def get_version(self):
        pass

    def get_collector_info_from_os(self):
        pass

    def stop_collector(self, password: str):
        pass

    def start_collector(self):
        pass

    def is_up(self):
        pass

    def upgrade(self):
        pass

    def is_installed(self):
        pass

    def is_enabled(self):
        pass

    def has_crash(self):
        pass

    def has_crash_dumps(self, append_to_report: bool):
        pass

    def copy_installation_files_to_local_machine(self, version: str):
        pass

    def get_collector_status(self):
        pass

    def validate_collector_is_up_and_running(self, use_health_monitor: bool = False):
        pass

    def start_health_mechanism(self):
        pass

    def install_collector(self, version: str, aggregator_ip: str, organization: str = None, aggregator_port: int = 8081,
                          registration_password: str = '12345678', append_log_to_report=True):
        pass

    def uninstall_collector(self, registration_password: str = '12345678', append_log_to_report=True):
        pass
