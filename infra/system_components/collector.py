from abc import abstractmethod
import logging
from typing import List
import allure

import third_party_details
from infra.enums import FortiEdrSystemState
from infra.system_components.collectors.default_values import COLLECTOR_KEEPALIVE_INTERVAL, MAX_WAIT_FOR_STATUS
from infra.common_utils import wait_for_condition
logger = logging.getLogger(__name__)

FILENAME_EDR_TESTER = "edrTester.py"


class CollectorAgent:
    """ An interface to implement collector agent on: Mac/Windows/Linux """
    def __init__(self, host_ip: str):
        self._host_ip = host_ip

    def __repr__(self):
        return f"Collector Agent on  {self._host_ip}"

    @property
    @abstractmethod
    def os_station(self):
        pass

    @property
    def host_ip(self) -> str:
        return self._host_ip

    @property
    @abstractmethod
    def initial_version(self) -> str:
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
    def get_agent_status(self) -> FortiEdrSystemState:
        pass

    @abstractmethod
    def get_configuration_files_details(self) -> List[dict]:
        """
        return these data of the configuration files: names, sizes, datetime
        """
        pass

    @abstractmethod
    def get_the_latest_config_file_details(self) -> dict:
        """
        return these data of the latest created configuration file: names, sizes, datetime
        """
        pass

    @abstractmethod
    def wait_for_new_config_file(self, latest_config_file_details=None):
        """
        wait until a new latest configuration file details received
        """
        pass

    def is_agent_installed(self) -> bool:
        pid = self.get_current_process_id()
        if pid is None and not self.is_collector_files_exist():
            return False

        return True

    def is_agent_running(self):
        return self.get_agent_status() == FortiEdrSystemState.RUNNING

    def is_agent_isolated(self):
        return self.get_agent_status() == FortiEdrSystemState.ISOLATED

    @allure.step("Wait until agent is running")
    def wait_until_agent_running(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is running")
        wait_for_condition(condition_func=self.is_agent_running, timeout_sec=timeout_sec,
                           interval_sec=interval_sec, condition_msg=f"{self} is running")

    @allure.step("Wait until agent is isolated")
    def wait_until_agent_isolated(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is isolated")
        wait_for_condition(condition_func=self.is_agent_isolated, timeout_sec=timeout_sec,
                           interval_sec=interval_sec, condition_msg=f"{self} is isolated")

    def is_agent_down(self):
        return self.get_agent_status() == FortiEdrSystemState.DOWN

    @allure.step("Wait until agent is down")
    def wait_until_agent_down(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is down")
        wait_for_condition(condition_func=self.is_agent_down, timeout_sec=timeout_sec,
                           interval_sec=interval_sec, condition_msg=f"{self} is down")

    def is_agent_disabled(self):
        return self.get_agent_status() == FortiEdrSystemState.DISABLED

    @allure.step("Wait until agent is disabled")
    def wait_until_agent_disabled(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is disabled")
        wait_for_condition(condition_func=self.is_agent_disabled, timeout_sec=timeout_sec,
                           interval_sec=interval_sec, condition_msg=f"{self} is disabled")

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

    def copy_log_parser_to_machine(self):
        pass

    @abstractmethod
    def install_collector(self, version: str, aggregator_ip: str, organization: str, registration_password: str):
        pass

    @abstractmethod
    def uninstall_collector(self, registration_password: str, stop_collector: bool = False):
        pass

    @abstractmethod
    def is_collector_files_exist(self) -> bool:
        pass

    def clear_logs(self):
        pass

    @abstractmethod
    def get_logs_content(self, file_suffix='.blg', filter_regex: str = None):
        pass

    def append_logs_to_report(self, first_log_timestamp_to_append, file_suffix='.blg'):
        pass

    def get_parsed_logs_after_specified_time_stamp(self, first_log_timestamp_to_append: str, file_suffix='.blg'):
        pass

    def create_event(self):
        pass

    @abstractmethod
    def remove_all_crash_dumps_files(self):
        pass

    @abstractmethod
    def create_bootstrap_backup(self, reg_password, filename=None):
        pass

    @abstractmethod
    def restore_bootstrap_file(self, full_path_filename):
        pass

    @allure.step("Preperation of EDR event tester working path")
    def prepare_edr_event_tester_folder(self, network_path: str, filename: str):
        """
            This function will copy and extract edr event tester into specific folder and return the extracted folder.
        """
        copied_path = self.os_station.copy_files_from_shared_folder(
            target_path_in_local_machine=self.get_qa_files_path(),
            shared_drive_path=network_path,
            files_to_copy=[filename],
            shared_drive_user_name=third_party_details.USER_NAME,
            shared_drive_password=third_party_details.PASSWORD)

        extracted_path = self.os_station.extract_compressed_file(
            file_path_to_extract=copied_path,
            file_name=filename)
        return extracted_path

    @abstractmethod
    def config_edr_simulation_tester(self, simulator_path, reg_password):
        pass

    @abstractmethod
    def start_edr_simulation_tester(self, simulator_path):
        pass

    @abstractmethod
    def cleanup_edr_simulation_tester(self, edr_event_tester_path, filename):
        """This function performs a cleanup of the leftovers of the EDR event tester."""
        pass
