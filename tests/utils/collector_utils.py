import allure
import logging
from infra.system_components.collector import CollectorAgent
from infra.multi_tenancy.tenant import Tenant
from infra import common_utils
logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 5
STATUS_TIMEOUT = 5 * 60
MAX_WAIT_FOR_CONFIGURATION = 5 * 60  # Arbitrary value


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

    @staticmethod
    @allure.step("Wait for configuration")
    def wait_for_configuration(collector_agent: CollectorAgent, tenant: Tenant, start_collector=True,
                               timeout=None, interval_sec=None):
        """ Wait until collector agent get updated configuration: the indication is a successful stop action
        with the updated registration password """
        timeout = timeout or MAX_WAIT_FOR_CONFIGURATION
        interval_sec = interval_sec or KEEPALIVE_INTERVAL
        logger.info(f"Wait until {collector_agent} will get the new configuration")
        rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
        registration_password = tenant.organization.registration_password

        def condition():
            try:
                logger.info(f"Try to stop collector with the updated registration password {registration_password}")
                collector_agent.stop_collector(password=registration_password)
                return True
            except Exception as e:
                logger.info(f"Failed to stop collector, try again. Got: {e}")
                return False

        common_utils.wait_for_condition(condition_func=condition, timeout_sec=timeout, interval_sec=interval_sec)
        collector_agent.wait_until_agent_down()
        if start_collector:
            collector_agent.start_collector()
            collector_agent.wait_until_agent_running()
            rest_collector.wait_until_running()


