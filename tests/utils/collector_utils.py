import allure
import time
import logging
from infra.system_components.collector import CollectorAgent
from infra.api.management_api.collector import RestCollector
from infra.multi_tenancy.tenant import Tenant
from infra import common_utils
from infra.system_components.management import Management
from infra.api.management_api.policy import WAIT_AFTER_ASSIGN
logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 5
STATUS_TIMEOUT = 5 * 60
MAX_WAIT_FOR_CONFIGURATION = 5 * 60  # Arbitrary value


class CollectorUtils:

    @staticmethod
    @allure.step("move collector to new group and assign group to policies")
    def move_collector_and_assign_group_policies(management: Management, collector, group_name: str):
        tenant = management.tenant
        user = tenant.default_local_admin
        rest_collector = user.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        rest_collector.move_to_different_group(target_group_name=group_name)
        default_policies = tenant.get_default_policies()
        for policy in default_policies:
            policy.assign_to_collector_group(group_name=group_name, wait_sec=1)
        time.sleep(WAIT_AFTER_ASSIGN)

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

    @staticmethod
    @allure.step("Validate collector installed successfully- basic validation")
    def validate_collector_installed_successfully(tenant: Tenant, collector_agent: CollectorAgent, expected_version):
        logger.info(f"Validate {collector_agent} installed successfully- basic validation")
        rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
        rest_collector.wait_until_running()
        collector_agent.wait_until_agent_running()
        assert collector_agent.get_version() == expected_version, \
            f"{collector_agent} version is {collector_agent.get_version()} instead of {expected_version}"
        assert collector_agent.is_collector_files_exist(), f"Installation folder was not created"

    @staticmethod
    @allure.step("Wait until rest collector is off in management")
    def wait_until_rest_collector_is_off(rest_collector: RestCollector):
        """ In collector version 6 the status changed from disconnected
        to degraded (when collector is stopped/uninstalled) """
        logger.info(f"Wait until {rest_collector} is off in management")
        os = rest_collector.get_operating_system(from_cache=False)
        collector_version = rest_collector.get_version(from_cache=False)
        if collector_version.startswith("6.") and "windows" in os.lower():
            rest_collector.wait_until_degraded()
        else:
            rest_collector.wait_until_disconnected()
