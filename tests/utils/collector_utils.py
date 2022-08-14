from enum import Enum
import allure
from contextlib import contextmanager
import time
import logging
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.api.management_api.collector import RestCollector
from infra.multi_tenancy.tenant import Tenant
from infra import common_utils
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.management import Management
from infra.api.management_api.policy import WAIT_AFTER_ASSIGN
from infra.utils.utils import StringUtils
from tests.utils.policy_utils import WINDOWS_MALWARES_NAMES


logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 5
STATUS_TIMEOUT = 5 * 60
MAX_WAIT_FOR_CONFIGURATION = 5 * 60  # Arbitrary value
MIN_FULL_CONFIG_SIZE_IN_KB = 15000
MAX_WAIT_FOR_CONFIG_FILE_TO_APPEAR = 60


class ConfigurationTypes(Enum):
    PARTIAL = 'Partial'
    FULL = 'Full'


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
    @allure.step("Validate collector installed successfully")
    def validate_collector_installed_successfully(tenant: Tenant, collector_agent: CollectorAgent, expected_version,
                                                  expected_package_name=None):
        logger.info(f"Validate {collector_agent} installed successfully")
        rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
        logger.info(f"Validate {collector_agent} status CLI & Management")
        rest_collector.wait_until_running()
        collector_agent.wait_until_agent_running()

        logger.info(f"Validate {collector_agent} installed version, expected {expected_version}")
        assert collector_agent.get_version() == expected_version, \
            f"{collector_agent} version is {collector_agent.get_version()} instead of {expected_version}"

        logger.info(f"Validate {collector_agent} installation folder")
        assert collector_agent.is_collector_files_exist(), f"Installation folder was not created"

        if isinstance(collector_agent, LinuxCollector):
            logger.info(f"Validate {collector_agent} installed package name")
            assert expected_package_name is not None, "Must provide package name"
            installed_package_name = collector_agent.get_package_name()
            assert installed_package_name == expected_package_name, \
                f"{collector_agent} Package name is '{installed_package_name}' instead of '{expected_package_name}'"

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


@contextmanager
def revive_collector_agent_on_failure_context(tenant: Tenant, collector_agent: CollectorAgent, aggregator):
    """ Revive collector agent only if there is an exception in the body of this context """
    collector_version = collector_agent.get_version()
    package_name = None
    if isinstance(collector_agent, LinuxCollector):
        package_name = collector_agent.get_package_name()
    try:
        yield
    except Exception as original_exception:
        try:
            logger.info(f"Test Failed ! got: \n {original_exception} \n Now Try to revive {collector_agent}")
            install_collector_if_not_installed(tenant=tenant, collector_agent=collector_agent, aggregator=aggregator,
                                               expected_version=collector_version, expected_package_name=package_name)
            start_collector_agent_if_is_down(tenant=tenant, collector_agent=collector_agent)
            enable_collector_agent_if_is_disabled(tenant=tenant, collector_agent=collector_agent)
            assert collector_agent.is_agent_installed(), f"{collector_agent} is not installed after revive"
            assert collector_agent.is_agent_running(), f"{collector_agent} is not running after revive"
        except Exception as revive_exception:
            logger.info(f"Failed to revive {collector_agent} !!!! Got {revive_exception}")
            assert False, f"Failed to revive {collector_agent} !!!! Got {revive_exception}"
        finally:
            assert False, f"Tried revive {collector_agent} because Test failed on exception: \n {original_exception}"  # validate exeption is raised


def install_collector_if_not_installed(tenant: Tenant, collector_agent: CollectorAgent,
                                       aggregator, expected_version, expected_package_name=None):
    logger.info(f"Check if {collector_agent} is installed, if not so install it")
    if not collector_agent.is_agent_installed():
        logger.info(f"{collector_agent} is not installed, install it version {expected_version} and validate")
        collector_agent.install_collector(version=expected_version,
                                          aggregator_ip=aggregator.host_ip,
                                          organization=tenant.organization.get_name(),
                                          registration_password=tenant.organization.registration_password)
        CollectorUtils.validate_collector_installed_successfully(tenant=tenant, collector_agent=collector_agent,
                                                                 expected_version=expected_version,
                                                                 expected_package_name=expected_package_name)
    else:
        logger.info(f"{collector_agent} is installed, validate that version is {expected_version}")
        current_version = collector_agent.get_version()
        assert current_version == expected_version, \
            f"{collector_agent} is installed but version is {current_version} instead of {expected_version}"


def start_collector_agent_if_is_down(tenant: Tenant, collector_agent: CollectorAgent):
    logger.info(f"Check if {collector_agent} is down, start it and validate")
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    if collector_agent.is_agent_down():
        logger.info(f"{collector_agent} is down, start it and validate")
        collector_agent.start_collector()
        collector_agent.wait_until_agent_running()
        rest_collector.wait_until_running()
    else:
        logger.info(f"{collector_agent} is not down, it is: {collector_agent.get_agent_status()}")


def enable_collector_agent_if_is_disabled(tenant: Tenant, collector_agent: CollectorAgent):
    logger.info(f"Check if {collector_agent} is disabled, enable it via management and validate")
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    if collector_agent.is_agent_disabled():
        logger.info(f"{collector_agent} is disabled, enable it via management and validate")
        rest_collector.enable()
        collector_agent.wait_until_agent_running()
        rest_collector.wait_until_running()
    else:
        logger.info(f"{collector_agent} is not disabled, it is: {collector_agent.get_agent_status()}")


@allure.step("Isolate collector rest_collector")
def isolate_collector(tenant: Tenant, collector_agent: CollectorAgent):
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    logger.info(f"Isolate collector {rest_collector}")
    rest_collector.isolate()
    rest_collector.wait_until_isolated()
    collector_agent.wait_until_agent_isolated()
    time.sleep(MAX_WAIT_FOR_CONFIG_FILE_TO_APPEAR)


@allure.step("Remove collector_agent from isolation mode")
def remove_collector_from_isolation_mode(tenant: Tenant, collector_agent: CollectorAgent):
    rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
    logger.info(f"Remove {collector_agent} from isolation mode")
    rest_collector.remove_from_isolation()
    rest_collector.wait_until_running()
    collector_agent.wait_until_agent_running()


@contextmanager
def isolate_collector_context(tenant: Tenant, collector_agent: CollectorAgent):
    with allure.step("Setup - Isolate collector"):
        rest_collector = tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
        assert rest_collector.is_running(), f"{rest_collector} is not running, it must to run before isolation." \
                                            f" current status is:{rest_collector.get_status()}"
        isolate_collector(tenant=tenant, collector_agent=collector_agent)
    try:
        yield
    finally:
        with allure.step("Cleanup - Remove collector from isolation mode"):
            if collector_agent.is_agent_isolated():
                remove_collector_from_isolation_mode(tenant=tenant, collector_agent=collector_agent)


def is_config_file_is_partial_or_full(collector: CollectorAgent, config_file_details: dict, first_log_date_time, config_type) -> bool:
    is_received_in_logs = False
    logger.info(f"Get parsed logs from {first_log_date_time}")
    log_files_dict = collector.get_parsed_logs_after_specified_time_stamp(first_log_timestamp_to_append=first_log_date_time,
                                                                          file_suffix='.blg')
    logger.info(f"Checking if {config_type} configuration received in the parsed logs")
    for file_name, file_content in log_files_dict.items():
        result = StringUtils.get_txt_by_regex(text=file_content, regex=f'Received {config_type} configuration update version', group=0)
        if result is not None:
            is_received_in_logs = True
            logger.info(f"Received from '{file_name}' log file: {result}")
            break
    if config_type == ConfigurationTypes.PARTIAL:
        return is_received_in_logs and config_file_details['file_size'] < MIN_FULL_CONFIG_SIZE_IN_KB
    elif config_type == ConfigurationTypes.FULL:
        return is_received_in_logs and config_file_details['file_size'] >= MIN_FULL_CONFIG_SIZE_IN_KB
    else:
        return False


@allure.step("Notify/Kill processes of malwares that are running on windows collector")
def notify_or_kill_malwares_on_windows_collector(collector_agent: CollectorAgent, safe=False):
    """ Search for a malware, if found: if safe is true so kill this malware.
    Otherwise, don't kill malware and raise an exception that collector contains a malware """
    running_malwares_names = []
    assert isinstance(collector_agent, WindowsCollector), "The collector must be of type windows"
    logger.info(f"Kill {WINDOWS_MALWARES_NAMES} processes that running on {collector_agent}")
    for windows_malware_name in WINDOWS_MALWARES_NAMES:
        pids = collector_agent.os_station.get_service_process_ids(windows_malware_name)
        if pids is not None:
            running_malwares_names.append(windows_malware_name)
            logger.info(f"Kill malware '{windows_malware_name}' that is running on {collector_agent}, pids are {pids}")
            for pid in pids:
                collector_agent.os_station.kill_process_by_id(pid=pid)
            with allure.step(f"Validate that malware '{windows_malware_name}' has no pid"):
                assert collector_agent.os_station.get_service_process_ids(windows_malware_name) is None, \
                      f"ERROR- failed to kill malware '{windows_malware_name}'"
    if len(running_malwares_names):
        assert safe, f"Found and killed these malwares: {running_malwares_names}, " \
                     f"probably one of previous test ended without kill the malwares"
