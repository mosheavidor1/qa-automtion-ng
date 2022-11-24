from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import datetime
import time

from infra.allure_report_handler.reporter import TEST_STEP, Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from tests.utils.collector_utils import revive_collector_agent_on_failure_context, CollectorUtils
from tests.utils.management_utils import restore_config_files, ManagementUtils, logger

TIMEOUT_COLLECTOR = 3 * 60
START_COLLECTOR_INTERVAL = 10
TIMEOUT_MANAGEMENT_START = 560


class UserRoleEnum(Enum):
    HOSTER_VIEW = 'hoster_view'
    ORGANIZATION_LOCAL_ADMIN = 'organization_local_admin'


@contextmanager
def move_collector_to_expired_mode_context(management: Management,
                                           collector: CollectorAgent,
                                           aggregator: Aggregator,
                                           ):
    try:
        application_properties_folder = '/opt/FortiEDR/webapp'
        application_properties_file = f'{application_properties_folder}/application.properties'
        application_customer_properties_file = f'{application_properties_folder}/application-customer.properties'
        config_files_to_manipulate = [application_properties_file, application_customer_properties_file]

        collector_agent = collector

        with restore_config_files(management=management, config_files=config_files_to_manipulate):
            with TEST_STEP("Change expire collector check interval to 1 minute in config files"):
                checking_interval_minutes = 1
                new_line_to_add = f"collector.expire.cron=0 0/{checking_interval_minutes} * 1/1 * ?"
                management.append_text_to_file(file_path=application_properties_file, content=new_line_to_add)
                management.append_text_to_file(file_path=application_customer_properties_file, content=new_line_to_add)

                management.restart_service()
                ManagementUtils.wait_till_operational(management=management)
            collector_host_name = collector.os_station.get_hostname()
            checking_interval_minutes = 1
            time_to_sleep_before_validation = checking_interval_minutes * 60 + 2

            # maybe we will need to perform a change here in 6.0.0.x version or above
            # because of new "keep alive" feature, need to perform operation that the management will think that
            # collector is disconnected
            rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
            collector.stop_collector(password=management.tenant.organization.registration_password)

            # logger.info("wait till collector service stopped in OS")
            # collector_agent.wait_until_agent_down()

            logger.info("wait till collector appears as Disconnected (expired) in management")
            CollectorUtils.wait_until_rest_collector_is_off(rest_collector=rest_collector)
            with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
                                                           aggregator=aggregator):
                with TEST_STEP("Change collector to expired mode via changing few columns in dev_agents table in DB"):
                    now = datetime.datetime.today()
                    then = now - datetime.timedelta(days=40)
                    then = then.strftime('%Y-%m-%d')
                    logger.info(f"convert {then} to epochtime")
                    date = datetime.datetime.strptime(then, "%Y-%m-%d")
                    epoch_time = datetime.datetime(date.year, date.month, date.day, date.hour, date.second).timestamp()
                    epoch_time = str(epoch_time).replace('.', '')
                    epoch_time += '00'

                    logger.info("Stop management server")
                    management.stop_service()
                    management.postgresql_db.execute_sql_command(
                        f"UPDATE dev_agents SET last_status_change = {epoch_time}, real_last_status_change = {epoch_time} WHERE host_name = '{collector_host_name}';")
                    logger.info("Start management server")
                    management.start_service()
                    ManagementUtils.wait_till_operational(management=management)

                    Reporter.report(
                        "Going to sleep 62 seconds in before validation (management is checking for expired collector each 60 sec)")
                    time.sleep(
                        time_to_sleep_before_validation)  # num of minutes * seconds + 2 seconds to avoid raise # condition

            yield  # go to world test

    finally:
        with TEST_STEP('Start collector agent'):
            collector.start_collector()
            collector.wait_until_agent_running()
            rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
            rest_collector.wait_until_running()
