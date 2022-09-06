import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter
import datetime
import logging
import time
from tests.utils.collector_utils import CollectorUtils, revive_collector_agent_on_failure_context
from tests.utils.management_utils import restore_config_files, ManagementUtils

logger = logging.getLogger(__name__)

@allure.epic("Management")
@allure.feature("Expired Collector")
# @pytest.mark.management_sanity
# @pytest.mark.management_full_regression
# @pytest.mark.full_regression
# @pytest.mark.xray('EN-70289')
def test_expired_collector(management, collector, aggregator):
    """
    !!! There is a bug - unstable, for questions please contact Leonid or Miri !!!
    1. Observe the capacity of license in use before making collector expired
    2. change collector to expired mode via manipulation dev_agents table in management DB
    3. wait until collector will be expired in manager
    4. perform API call again in order to check the license status again - validate 1 license was released
    5. finally - bring up collector again at the end of the test
    6. perform API call again in order to check the license status again - validate 1 license was occupied again.
    """

    application_properties_folder = '/opt/FortiEDR/webapp'
    application_properties_file = f'{application_properties_folder}/application.properties'
    application_customer_properties_file = f'{application_properties_folder}/application-customer.properties'
    config_files_to_manipulate = [application_properties_file, application_customer_properties_file]

    collector_agent = collector

    default_org = management.tenant.organization

    with restore_config_files(management=management, config_files=config_files_to_manipulate):

        with TEST_STEP("Change expire collector check interval to 1 minute in config files"):

            checking_interval_minutes = 1
            time_to_sleep_before_validation = checking_interval_minutes * 60 + 2

            new_line_to_add = f"collector.expire.cron=0 0/{checking_interval_minutes} * 1/1 * ?"
            management.append_text_to_file(file_path=application_properties_file, content=new_line_to_add)
            management.append_text_to_file(file_path=application_customer_properties_file, content=new_line_to_add)

            management.restart_service()
            ManagementUtils.wait_till_operational(management=management)

        with TEST_STEP(f"Observe the license status before making collector expired"):
            result_capacity_in_use_before_making_collector_expired = default_org.get_works_station_licences_in_use()
            Reporter.report(
                f"Current licenses in use before making collector expired = {result_capacity_in_use_before_making_collector_expired}",
                logger_func=logger.info)

        with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
                                                       aggregator=aggregator):
            with TEST_STEP("Make collector state disconnected"):
                collector_host_name = collector.os_station.get_hostname()

                # maybe we will need to perform a change here in 6.0.0.x version or above
                # because of new "keep alive" feature, need to perform operation that the management will think that
                # collector is disconnected
                rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
                collector_agent.stop_collector(password=management.tenant.organization.registration_password)

                # logger.info("wait till collector service stopped in OS")
                # collector_agent.wait_until_agent_down()

                logger.info("wait till collector appears as Disconnected (expired) in management")
                CollectorUtils.wait_until_rest_collector_is_off(rest_collector=rest_collector)

            with TEST_STEP("Change collector to expired mode via changing few columns in dev_agents table in DB"):
                now = datetime.datetime.today()
                then = now - datetime.timedelta(days=40)
                then = then.strftime('%Y-%m-%d')
                logger.info(f"convert {then} to epochtime")
                date = datetime.datetime.strptime(then,
                                                  "%Y-%m-%d")  # this is a problemtic row - understand why it failed
                epoch_time = datetime.datetime(date.year, date.month, date.day, date.hour, date.second).timestamp()
                epoch_time = str(epoch_time).replace('.', '')
                epoch_time += '00'

                logger.info("Stop management server")
                management.stop_service()
                management.postgresql_db.execute_sql_command(
                    f"UPDATE dev_agents SET last_status_change = {epoch_time}, real_last_status_change = {epoch_time} WHERE host_name = '{collector_host_name}';")
                # result = management.postgresql_db.execute_sql_command(f"SELECT id,host_name,last_status_change from dev_agents WHERE host_name = '{host_name}';")

                logger.info("Start management server")
                management.start_service()
                ManagementUtils.wait_till_operational(management=management)

                Reporter.report(
                    "Going to sleep 62 seconds in before validation (management is checking for expired collector each 60 sec)")
                time.sleep(
                    time_to_sleep_before_validation)  # num of minutes * seconds + 2 seconds to avoid raise condition

            with TEST_STEP(
                    f"perform API call again in order to check the license status again - validate it's as expected"):
                # TODO: Verify expected collector is expired == 1
                # TODO: Licence released and not caught by expired (Remaining = 100)
                result_capacity_in_use_after_making_collector_expired = default_org.get_works_station_licences_in_use()
                Reporter.report(
                    f"Current licenses in use after making collector expired = {result_capacity_in_use_after_making_collector_expired}",
                    logger_func=logger.info)
                Reporter.report(f"check the license status again - validate it's as expected")

                if result_capacity_in_use_before_making_collector_expired - result_capacity_in_use_after_making_collector_expired != 1:
                    assert False, f"Collector is in expired state but still use license"
                else:
                    Reporter.report(
                        "Management release 1 license as expceted (1 expired collector = 1 release license)",
                        logger_func=logger.info)

            with TEST_STEP('Start collector agent'):
                collector_agent.start_collector()
                collector_agent.wait_until_agent_running()
                rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector_agent.host_ip)
                rest_collector.wait_until_running()

            with TEST_STEP('Validate license was occupied again'):
                time.sleep(time_to_sleep_before_validation)
                result_capacity_after_making_collector_live = default_org.get_works_station_licences_in_use()
                if result_capacity_in_use_before_making_collector_expired != result_capacity_after_making_collector_live:
                    assert False, f"Expecting in use license = {result_capacity_in_use_before_making_collector_expired}, actual = {result_capacity_after_making_collector_live}"

                else:
                    Reporter.report("Number of license in use = 1 as expected", logger_func=logger.info)
