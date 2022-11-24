from datetime import datetime
from infra.api import ADMIN_REST
from tests.utils.expired_collector_utils import UserRoleEnum, move_collector_to_expired_mode_context
import logging
import allure
import pytest
from infra.allure_report_handler.reporter import TEST_STEP, Reporter
from infra.containers.extracted_licenes_status import LicenseStatus
from infra.utils.utils import StringUtils
from tests.utils.collector_utils import logger
import datetime
import time

logger = logging.getLogger(__name__)


@allure.epic("Management")
@allure.feature("Expired Collector")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.e2e_linux_collector_sanity
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.management_sanity
@pytest.mark.management_full_regression
@pytest.mark.expired_collector
@pytest.mark.expired_collector_sanity
@pytest.mark.parametrize(
    "xray, user_role",
    [('EN-70360', UserRoleEnum.ORGANIZATION_LOCAL_ADMIN.value),
     ('EN-70289', UserRoleEnum.HOSTER_VIEW.value)],
)
def test_expired_collector(management, collector, aggregator, xray, user_role):
    """
     Test that changing the collector status to expired creates the desired changes

        1. Observe the capacity of license in use before making collector expired
        2. change collector to expired mode via manipulation dev_agents table in management DB
        3. wait until collector will be expired in manager
        4. perform API call again in order to check the license status again - validate 1 license was released
        5. finally - bring up collector again at the end of the test
        6. perform API call again in order to check the license status again - validate 1 license was occupied again.
    """

    default_org = management.tenant.organization
    mgmt_logs_datetime_format = "%Y-%m-%d %H:%M:%S"
    collector_host_name = collector.os_station.get_hostname()
    checking_interval_minutes = 1
    time_to_sleep_before_validation = checking_interval_minutes * 60 + 2

    if 'server' or 'centos' or 'ubuntu' in collector.os_station.os_name.lower():
        collector_type = 'server'
    elif 'windows' in collector.os_station.os_name.lower():
        collector_type = 'workstation'
    else:
        raise Exception(f"This type is not supported: {collector.os_station.os_name}")

    with TEST_STEP(f"Observe the license status before making collector expired"):
        if user_role == UserRoleEnum.ORGANIZATION_LOCAL_ADMIN.value:
            result_capacity_in_use_before_making_collector_expired = {
                'workstations': default_org.get_works_station_licences_in_use(),
                'servers': default_org.get_servers_licences_in_use()}
        elif user_role == UserRoleEnum.HOSTER_VIEW.value:
            system_summary = ADMIN_REST().administrator.get_system_summery()
            result_capacity_in_use_before_making_collector_expired = {'workstations': system_summary.get(
                'workstationsCollectorsInUse'), 'servers': system_summary.get(
                'serverCollectorsInUse')}
        else:
            raise Exception(f"This test does not support the argument: {user_role}")

        Reporter.report(
            f"Current licenses in use before making collector expired = {result_capacity_in_use_before_making_collector_expired}",
            logger_func=logger.info)

    time_changing_the_status_to_expired_in_management = management.get_current_machine_datetime(
        date_format=mgmt_logs_datetime_format)
    with move_collector_to_expired_mode_context(management=management,
                                                collector=collector,
                                                aggregator=aggregator
                                                ):
        with TEST_STEP(
                f"perform API call again in order to check the license status again - validate it's as expected"):
            if user_role == UserRoleEnum.ORGANIZATION_LOCAL_ADMIN.value:
                result_capacity_in_use_after_making_collector_expired = {
                    'workstations': default_org.get_works_station_licences_in_use(),
                    'servers': default_org.get_servers_licences_in_use()}
            elif user_role == UserRoleEnum.HOSTER_VIEW.value:
                system_summary = ADMIN_REST().administrator.get_system_summery()
                result_capacity_in_use_after_making_collector_expired = {'workstations': system_summary.get(
                    'workstationsCollectorsInUse'), 'servers': system_summary.get(
                    'serverCollectorsInUse')}
            else:
                raise Exception(f"this test does not support the argument: {user_role}")

            Reporter.report(
                f"Current licenses in use after making collector expired = {result_capacity_in_use_after_making_collector_expired}",
                logger_func=logger.info)

            with TEST_STEP(
                    "Calculate license capacity according to OS"):
                if collector_type == 'workstation':
                    capacity_left = result_capacity_in_use_before_making_collector_expired.get(
                        'workstations') - result_capacity_in_use_after_making_collector_expired.get(
                        'workstations')
                else:
                    capacity_left = result_capacity_in_use_before_making_collector_expired.get(
                        'servers') - result_capacity_in_use_after_making_collector_expired.get('servers')

                Reporter.report(
                    f"Check that the license has one more capacity seat according to OS, capacity left = {capacity_left}",
                    logger_func=logger.info)

                if capacity_left != 1:
                    assert False, f"Collector is in expired state but license still counts collector as used"
                else:
                    Reporter.report(
                        "Management released 1 license as expected (1 expired collector = 1 release license)",
                        logger_func=logger.info)

        if user_role == UserRoleEnum.ORGANIZATION_LOCAL_ADMIN.value:
            with TEST_STEP(
                    f"verify a new event with the correct collector name was created with this description: "
                    f"Collector [{collector_host_name}] state was changed to 'disconnected (expired) in the same time "
                    f"frame"):
                user = management.tenant.rest_components

                time_changing_the_status_to_expired_in_management_format = datetime.datetime.strptime(
                    time_changing_the_status_to_expired_in_management, mgmt_logs_datetime_format)
                latest_system_events_date_in_specific_component_name = user.system_event.get_the_latest_date(
                    component_name=collector_host_name)
                time_changing_the_status_to_expired_in_management_plus_10 = time_changing_the_status_to_expired_in_management_format + datetime.timedelta(
                    minutes=10)
                date_event = latest_system_events_date_in_specific_component_name[0].get_date()
                if time_changing_the_status_to_expired_in_management_format <= date_event <= time_changing_the_status_to_expired_in_management_plus_10:
                    assert True, "A suitable event is found within the desired minutes"
                else:
                    assert False, "didn't find any event with this range of time"

                description_system_event = latest_system_events_date_in_specific_component_name[
                    0].get_description(
                    from_cache=False)
                statement_to_check = f'Collector [{collector_host_name}] state was changed to "disconnected (' \
                                     f'expired)"'
                if statement_to_check != description_system_event:
                    assert False, f"didn't find any event with {description_system_event} description"

            # with TEST_STEP('Validate no errors and exceptions in logs'):
            #     # mgmt_logs_datetime_format = "%Y-%m-%d %H:%M:%S"
            #     # test_start_time_in_management = management.get_current_machine_datetime(date_format=mgmt_logs_datetime_format)
            #
            #     test_start_time_in_management = test_start_time_in_management
            #
            #     machine_timestamp_date_format = '%Y-%m-%d %H:%M:%S'
            #     log_timestamp_date_format = '%Y-%m-%d %H:%M:%S'
            #     log_timestamp_date_format_regex_linux = '[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
            #     log_file_datetime_regex_python = '(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)'
            #
            #     result = management.is_string_exist_in_logs(
            #         string_to_search="error",
            #         first_log_timestamp=test_start_time_in_management,
            #         machine_timestamp_date_format=machine_timestamp_date_format,
            #         log_timestamp_date_format=log_timestamp_date_format,
            #         log_timestamp_date_format_regex_linux=log_timestamp_date_format_regex_linux,
            #         log_file_datetime_regex_python=log_file_datetime_regex_python)
            #     if result == True:
            #         assert False, "found exception in logs"

    with TEST_STEP('Validate license was occupied again'):
        time.sleep(time_to_sleep_before_validation)
        if user_role == UserRoleEnum.ORGANIZATION_LOCAL_ADMIN.value:
            result_capacity_after_making_collector_live = {
                'workstations': default_org.get_works_station_licences_in_use(),
                'servers': default_org.get_servers_licences_in_use()}
        elif user_role == UserRoleEnum.HOSTER_VIEW.value:
            system_summary = ADMIN_REST().administrator.get_system_summery()
            result_capacity_after_making_collector_live = {'workstations': system_summary.get(
                'workstationsCollectorsInUse'), 'servers': system_summary.get(
                'serverCollectorsInUse')}
        else:
            raise Exception(f"this test does not support the argument: {user_role}")

        if result_capacity_in_use_before_making_collector_expired.get(
                'workstations') != result_capacity_after_making_collector_live.get(
            'workstations') | result_capacity_in_use_before_making_collector_expired.get(
            'servers') != result_capacity_after_making_collector_live.get('servers'):
            assert False, f"Expecting in use license = workstations: " \
                          f"{result_capacity_in_use_before_making_collector_expired.get('workstations')} severs: " \
                          f"{result_capacity_in_use_before_making_collector_expired.get('servers')} , actual = workstations: " \
                          f"{result_capacity_after_making_collector_live.get('workstations')}, servers: " \
                          f"{result_capacity_after_making_collector_live.get('servers')}"

        else:
            Reporter.report("Number of license in use = 1 as expected", logger_func=logger.info)


@allure.epic("Management")
@allure.feature("Expired Collector")
@pytest.mark.expired_collector
@pytest.mark.expired_collector_sanity
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.xray('EN-69950')
def test_expired_collector_change_status_back_to_running(management, collector, aggregator):
    """
      this test run by TESTIM
    1. Observe the capacity of license in use before making collector expired
    2. change collector to expired mode via manipulation dev_agents table in management DB
    3. wait until collector will be expired in manager
    4. check the license status again - validate 1 license was released
    5. finally - bring up collector again at the end of the test
    6. check the license status again - validate 1 license was occupied again.
    """

    collector_host_name = collector.os_station.get_hostname()
    checking_interval_minutes = 1
    time_to_sleep_before_validation = checking_interval_minutes * 60 + 2

    with TEST_STEP(f"Observe the license status before making collector expired via TESTIM"):
        output = management.ui_client.licenses.checking_licenses_status()
        workstations_in_use = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'workstationsInUse :\s+(\d+)', group=1))
        servers_in_use = int(StringUtils.get_txt_by_regex(text=output, regex=r'serversInUse :\s+(\d+)', group=1))
        workstations_remaining = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'workstationsRemaining :\s+(\d+)', group=1))
        servers_remaining = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'serversRemaining :\s+(\d+)', group=1))
        licenses_status_before_collector_expired = LicenseStatus(workstation_in_use=workstations_in_use,
                                                                 servers_in_use=servers_in_use,
                                                                 workstation_remaining=workstations_remaining,
                                                                 servers_remaining=servers_remaining)
        Reporter.report(
            f"Current licenses in use before making collector expired ="
            f" workstations:{licenses_status_before_collector_expired.workstation_in_use}"
            f"servers: {licenses_status_before_collector_expired.servers_in_use}",
            logger_func=logger.info)

    with move_collector_to_expired_mode_context(management=management, collector=collector,
                                                aggregator=aggregator
                                                ):
        with TEST_STEP("verify collector is disconnected-expired via TESTIM"):
            management.ui_client.inventory.verify_collector_is_disconnected_expired(
                {"targetCollector": collector_host_name})

        with TEST_STEP(
                f"check the license status again when the collector is dissconnected-expired via TESTIM - "
                f"validate it's as expected"):
            output = management.ui_client.licenses.checking_licenses_status()
            workstations_in_use = int(
                StringUtils.get_txt_by_regex(text=output, regex=r'workstationsInUse :\s+(\d+)', group=1))
            servers_in_use = int(
                StringUtils.get_txt_by_regex(text=output, regex=r'serversInUse :\s+(\d+)', group=1))
            workstations_remaining = int(
                StringUtils.get_txt_by_regex(text=output, regex=r'workstationsRemaining :\s+(\d+)', group=1))
            servers_remaining = int(
                StringUtils.get_txt_by_regex(text=output, regex=r'serversRemaining :\s+(\d+)', group=1))

            licenses_status_when_collector_expired = LicenseStatus(workstation_in_use=workstations_in_use,
                                                                   workstation_remaining=workstations_remaining,
                                                                   servers_in_use=servers_in_use,
                                                                   servers_remaining=servers_remaining)
            Reporter.report(
                f"Current licenses in use after making collector expired = workstations:{licenses_status_when_collector_expired.workstation_in_use} "
                f"servers: {licenses_status_when_collector_expired.servers_in_use}",
                logger_func=logger.info)

            Reporter.report(f"check the license status again - validate it's as expected")

            if licenses_status_before_collector_expired.workstation_in_use - licenses_status_when_collector_expired.workstation_in_use != 1 | licenses_status_before_collector_expired.servers_in_use - licenses_status_when_collector_expired.servers_in_use != 1:
                assert False, f"Collector is in expired state but still use license"
            else:
                Reporter.report(
                    "Management release 1 license as excepted (1 expired collector = 1 release license)",
                    logger_func=logger.info)

        with TEST_STEP('validate there is free licence to revive the expired collector'):
            if licenses_status_when_collector_expired.servers_remaining < 0 and licenses_status_when_collector_expired.workstation_remaining < 0:
                assert False, "there is no free license to revive collector"
            else:
                Reporter.report(
                    "there is free licence for the collector",
                    logger_func=logger.info)

    with TEST_STEP(f"Observe the license status after revive the expired collector via TESTIM"):
        output = management.ui_client.licenses.checking_licenses_status()
        workstations_in_use = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'workstationsInUse :\s+(\d+)', group=1))
        servers_in_use = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'serversInUse :\s+(\d+)', group=1))
        workstations_remaining = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'workstationsRemaining :\s+(\d+)', group=1))
        servers_remaining = int(
            StringUtils.get_txt_by_regex(text=output, regex=r'serversRemaining :\s+(\d+)', group=1))
        licenses_status_when_collector_is_running = LicenseStatus(workstation_in_use=workstations_in_use,
                                                                  workstation_remaining=workstations_remaining,
                                                                  servers_in_use=servers_in_use,
                                                                  servers_remaining=servers_remaining)
    with TEST_STEP('Validate license was occupied again'):
        time.sleep(time_to_sleep_before_validation)
        if licenses_status_before_collector_expired.workstation_in_use != licenses_status_when_collector_is_running.workstation_in_use | licenses_status_before_collector_expired.servers_in_use != licenses_status_when_collector_is_running.servers_in_use:
            assert False, f"Expecting in use license = workstations: {licenses_status_before_collector_expired.workstation_in_use} , servers: {licenses_status_before_collector_expired.servers_in_use}, actual = workstations:{licenses_status_when_collector_expired.workstation_in_use} , servers: {licenses_status_when_collector_expired.servers_in_use}"

        else:
            Reporter.report("Number of license in use = 1 as expected", logger_func=logger.info)
