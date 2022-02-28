import allure
from datetime import datetime
from infra.enums import SystemState
from infra.system_components.collector import Collector

INSTALL_UNINSTALL_LOGS_FOLDER_PATH = "C:\\InstallUninstallLogs"


class CollectorUtils:

    @staticmethod
    @allure.step("{0} - Validate collector stopped")
    def validate_collector_stopped(collector: Collector):
        """ Validate that collector stopped:
        1. Collector should return correct status (not running).
        2. PID should be None.
        """
        pid = collector.get_current_process_id()
        assert collector.get_collector_status() == SystemState.NOT_RUNNING, \
            f"Collector on host {collector} was not stopped, pid is {pid}"
        assert pid is None, \
            f"Collector on host {collector} returning wrong status because pid {pid} still exists"

    @staticmethod
    @allure.step("{0} - Validate collector is currently running")
    def validate_collector_is_currently_running(collector: Collector):
        collector_status = collector.get_collector_status()
        assert collector_status == SystemState.RUNNING, f"{collector} is not running"

    @staticmethod
    @allure.step("Validate collector is currently running according to the management")
    def validate_collector_is_currently_running_according_to_management(management, collector: Collector):
        collector_status_management = management.get_collector_status(collector_ip=collector.os_station.host_ip)
        assert collector_status_management == SystemState.RUNNING, f"{collector} is not running"

    @staticmethod
    @allure.step("Validate that collector state is equal both on management and on the machine command line")
    def validate_collector_state_is_equal_both_on_machine_and_management(management, collector: Collector):
        # TODO - uncomment those rows when the system will work as expected
        collector_state_management = management.get_collector_state(collector_ip=collector.os_station.host_ip)
        collector_status_cli = collector.get_collector_status()

        if collector_state_management != collector_status_cli:
            assert False, f"State in Management is : {collector_state_management.name}, state from command line is: {collector_status_cli.name}"

    @staticmethod
    @allure.step("move collector to new group and assign group to policies")
    def move_collector_and_assign_group_policies(management, collector: Collector, group_name):
        management.rest_api_client.move_collector({'ipAddress': collector.os_station.host_ip}, group_name)
        management.rest_api_client.assign_policy('Exfiltration Prevention', group_name, timeout=1)
        management.rest_api_client.assign_policy('Execution Prevention', group_name, timeout=1)
        management.rest_api_client.assign_policy('Ransomware Prevention', group_name)

    @staticmethod
    def create_logs_path(collector: Collector, prefix):
        logs_file_name = f"{prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        logs_folder = collector.os_station.create_new_folder(fr'{INSTALL_UNINSTALL_LOGS_FOLDER_PATH}')
        logs_path = fr"{logs_folder}\{logs_file_name}"
        return logs_path

    @staticmethod
    def validate_installation_folder_is_empty(collector: Collector):
        is_empty = collector.is_installation_folder_empty()
        assert is_empty, f"Installation folder contains files, should be empty"
