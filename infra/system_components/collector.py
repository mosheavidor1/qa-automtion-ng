from abc import abstractmethod
from infra.containers.system_component_containers import CollectorDetails
from infra.enums import SystemState


class Collector:

    def __init__(self, host_ip: str):
        self._host_ip = host_ip

    def __repr__(self):
        return f"Collector  {self._host_ip}"

    @property
    @abstractmethod
    def os_station(self):
        pass

    @property
    @abstractmethod
    def details(self) -> CollectorDetails:
        pass

    @property
    @abstractmethod
    def cached_process_id(self) -> int:
        """ Caching the current process id in order later validate if it changed """
        pass

    @abstractmethod
    def get_version(self):
        pass

    @abstractmethod
    def stop_collector(self, password: str = None):
        pass

    @abstractmethod
    def start_collector(self):
        pass

    @abstractmethod
    def has_crash(self):
        pass

    @abstractmethod
    def has_crash_dumps(self, append_to_report: bool):
        pass

    @abstractmethod
    def get_collector_status(self) -> SystemState:
        pass

    @abstractmethod
    def is_status_running_in_cli(self):
        pass

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def update_process_id(self):
        """ Update the cached pid to the current pid """
        pass

    @abstractmethod
    def get_current_process_id(self):
        pass

    @abstractmethod
    def install_collector(self):
        pass

    def copy_log_parser_to_machine(self):
        pass

    @abstractmethod
    def uninstall_collector(self):
        pass

    def clear_logs(self):
        pass

    def append_logs_to_report(self, first_log_timestamp_to_append, file_suffix='.blg'):
        pass

    def create_event(self):
        pass

    @abstractmethod
    def remove_all_crash_dumps_files(self):
        pass
