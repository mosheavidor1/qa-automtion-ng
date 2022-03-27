import allure
from datetime import datetime
from infra.system_components.collector import Collector
from .test_utils import TestUtils

INSTALL_UNINSTALL_LOGS_FOLDER_PATH = "C:\\InstallUninstallLogs"
COLLECTOR_KEEPALIVE_INTERVAL = 5
MAX_WAIT_FOR_STATUS = 5 * 60


class CollectorUtils:

    @staticmethod
    @allure.step("Wait until status of {collector} in {management} is not running")
    def wait_for_not_running_collector_status_in_mgmt(management, collector, timeout=None):
        timeout = timeout or MAX_WAIT_FOR_STATUS

        def is_collector_status_not_running():
            is_not_running = not management.is_collector_status_running_in_mgmt(collector)
            return is_not_running
        TestUtils.wait_for_predict_condition(predict_condition_func=is_collector_status_not_running,
                                             timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)

    @staticmethod
    @allure.step("Wait until status of {collector} in cli is 'not running'")
    def wait_for_not_running_status_in_cli(collector, timeout=None):
        timeout = timeout or MAX_WAIT_FOR_STATUS

        def is_collector_status_not_running():
            is_not_running = not collector.is_status_running_in_cli()
            return is_not_running
        TestUtils.wait_for_predict_condition(predict_condition_func=is_collector_status_not_running,
                                             timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)

    @staticmethod
    @allure.step("Wait until status of {collector} in cli is 'down")
    def wait_for_service_down_status_in_cli(collector, timeout=None):
        timeout = timeout or MAX_WAIT_FOR_STATUS
        predict_condition_func = collector.is_status_down_in_cli
        TestUtils.wait_for_predict_condition(predict_condition_func=predict_condition_func,
                                             timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)

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
