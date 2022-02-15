from abc import abstractmethod

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.containers.system_component_containers import CollectorDetails
from infra.enums import OsTypeEnum, SystemState
from infra.os_stations.os_station_base import OsStation
from infra.system_components.os_station_factory import OsStationFactory


class Collector:

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 os_type: OsTypeEnum,
                 collector_details: CollectorDetails,
                 encrypted_connection: bool = True):
        self._os_station: OsStation = OsStationFactory.get_os_station_according_to_type(os_type=os_type,
                                                                                        host_ip=host_ip,
                                                                                        user_name=user_name,
                                                                                        password=password,
                                                                                        encrypted_connection=encrypted_connection)
        self._host_ip = host_ip
        self._user_name = user_name
        self._password = password
        self._details = collector_details
        self._process_id = self.get_current_process_id()

    def __repr__(self):
        return f"Collector  {self._host_ip}"

    @property
    def os_station(self) -> OsStation:
        return self._os_station

    @property
    def details(self) -> CollectorDetails:
        return self._details

    @details.setter
    def details(self, details: CollectorDetails):
        self._details = details

    @property
    def process_id(self) -> int:
        return self._process_id

    @abstractmethod
    def get_version(self):
        pass

    @abstractmethod
    def get_service_name(self):
        pass

    @abstractmethod
    def get_collector_info_from_os(self):
        pass

    @abstractmethod
    def get_qa_files_path(self):
        pass

    @abstractmethod
    def stop_collector(self, password: str):
        pass

    @abstractmethod
    def start_collector(self):
        pass

    @abstractmethod
    def is_up(self):
        pass

    @abstractmethod
    def upgrade(self):
        pass

    @abstractmethod
    def is_installed(self):
        pass

    @abstractmethod
    def is_enabled(self):
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
    def validate_collector_is_up_and_running(self, use_health_monitor: bool = False,
                                             timeout: int = 60,
                                             validation_delay: int = 5):
        pass

    @allure.step("Get current collector process ID")
    def get_current_process_id(self):
        service_name = self.get_service_name()
        process_ids = self.os_station.get_service_process_ids(service_name=service_name)
        process_id = process_ids[0]
        Reporter.report(f"Current process ID is: {process_id}")
        return process_id

    @allure.step("Update process ID in current collector object")
    def _update_process_id(self):
        Reporter.report(f"Current process ID is: {self._process_id}")
        self._process_id = self.get_current_process_id()
        Reporter.report(f"Collector process ID updated to: {self._process_id}")

    @abstractmethod
    def start_health_mechanism(self):
        pass

    @abstractmethod
    def install_collector(self,
                          version: str,
                          aggregator_ip: str,
                          organization: str = None,
                          aggregator_port: int = 8081,
                          registration_password: str = '12345678',
                          append_log_to_report=True):
        pass

    @abstractmethod
    def copy_log_parser_to_machine(self):
        pass

    @abstractmethod
    def uninstall_collector(self, registration_password: str = '12345678', append_log_to_report=True):
        pass

    @abstractmethod
    def clear_logs(self):
        pass

    @abstractmethod
    def append_logs_to_report(self, first_log_timestamp_to_append, file_suffix='.blg'):
        pass

    @abstractmethod
    def create_event(self, malware_name="DynamicCodeTests"):
        pass
