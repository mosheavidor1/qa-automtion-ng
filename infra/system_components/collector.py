from abc import abstractmethod
import logging
import allure
from infra.enums import FortiEdrSystemState
from infra.system_components.collectors.default_values import COLLECTOR_KEEPALIVE_INTERVAL, MAX_WAIT_FOR_STATUS
from infra.common_utils import wait_for_condition
logger = logging.getLogger(__name__)


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

    def is_agent_installed(self) -> bool:
        pid = self.get_current_process_id()
        if pid is None and not self.is_collector_files_exist():
            return False

        return True

    def is_agent_running(self):
        return self.get_agent_status() == FortiEdrSystemState.RUNNING

    @allure.step("Wait until agent is running")
    def wait_until_agent_running(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is running")
        wait_for_condition(condition_func=self.is_agent_running,
                           timeout_sec=timeout_sec, interval_sec=interval_sec)

    def is_agent_down(self):
        return self.get_agent_status() == FortiEdrSystemState.DOWN

    @allure.step("Wait until agent is down")
    def wait_until_agent_down(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is down")
        wait_for_condition(condition_func=self.is_agent_down,
                           timeout_sec=timeout_sec, interval_sec=interval_sec)

    def is_agent_disabled(self):
        return self.get_agent_status() == FortiEdrSystemState.DISABLED

    @allure.step("Wait until agent is disabled")
    def wait_until_agent_disabled(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is disabled")
        wait_for_condition(condition_func=self.is_agent_disabled,
                           timeout_sec=timeout_sec, interval_sec=interval_sec)

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

    def append_logs_to_report(self, first_log_timestamp_to_append, file_suffix='.blg'):
        pass

    def create_event(self):
        pass

    @abstractmethod
    def remove_all_crash_dumps_files(self):
        pass
