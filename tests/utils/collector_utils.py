import allure
import logging

logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 5
STATUS_TIMEOUT = 5 * 60


class CollectorUtils:

    @staticmethod
    @allure.step("move collector to new group and assign group to policies")
    def move_collector_and_assign_group_policies(management, collector, group_name: str):
        management.tenant.rest_api_client.system_inventory.move_collector(
            validation_data={'ipAddress': collector.os_station.host_ip},
            group_name=group_name)
        management.tenant.rest_api_client.policies.assign_policy('Exfiltration Prevention', group_name, timeout=1)
        management.tenant.rest_api_client.policies.assign_policy('Execution Prevention', group_name, timeout=1)
        management.tenant.rest_api_client.policies.assign_policy('Ransomware Prevention', group_name)
