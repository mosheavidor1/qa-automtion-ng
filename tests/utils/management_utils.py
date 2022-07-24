import time
from contextlib import contextmanager

import allure
import logging

from infra.allure_report_handler.reporter import TEST_STEP
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.assertion.assertion import Assertion, AssertTypeEnum
logger = logging.getLogger(__name__)


class ManagementUtils:

    @staticmethod
    @allure.step("create excepted event and check if created")
    def create_excepted_event_and_check(management: Management, collector: CollectorAgent, malware_name, expected_result):
        """
        create event with existing exception and check if created
        """
        user = management.tenant.default_local_admin
        user.rest_components.events.delete_all(safe=True)
        collector.create_event(malware_name=malware_name)
        if expected_result:
            events = user.rest_components.events.get_by_process_name(process_name=malware_name, wait_for=True)
        else:
            time.sleep(60)  # Sleep in order to be sure that event will not appear suddenly later in management
            events = user.rest_components.events.get_by_process_name(process_name=malware_name,
                                                                     safe=True, wait_for=False)

        is_event_created = True if events is not None and len(events) > 0 else False
        Assertion.invoke_assertion(expected=expected_result, actual=is_event_created,
                                   message=r"event was\wasn't created as expected",
                                   assert_type=AssertTypeEnum.SOFT)

    @staticmethod
    @allure.step("validate exception exists with given parameters")
    def validate_exception(management: Management, process: str, event_id=None, group='All Collector Groups',
                           destination='All Destinations', user='All Users', comment=None):
        admin_user = management.tenant.default_local_admin
        exceptions = admin_user.rest_components.exceptions.get_by_event_id(event_id=event_id, safe=True)
        if exceptions is None:
            return False
        for exception in exceptions:
            exception = exception.cache
            if process in str(exception) and \
                    group in exception['selectedCollectorGroups'] and \
                    destination in exception['selectedDestinations'] and \
                    user in exception['selectedUsers'] and \
                    (comment is None or comment in exception['comment']):
                return exception['exceptionId']
        return False

    @staticmethod
    @allure.step("Restart manager - wait until management is operational")
    def wait_till_operational(management: Management):
        management.wait_till_service_up(timeout=60, interval=5)
        management.wait_until_rest_api_available(timeout=60, interval=5)


@contextmanager
def restore_config_files(management: Management, config_files: [str]):

    try:
        # backup files
        with TEST_STEP("Save config files as backup"):
            for single_config_file in config_files:
                management.copy_files(source=single_config_file, target=f'{single_config_file}.backup')

        yield # go to tests world

    except Exception as original_exception:
        try:
            logger.info(f"Test Failed ! got: \n {original_exception} \n Now Try to restore the files: {config_files}")
            # restore files
            with TEST_STEP("Restore config files from backup"):
                for single_config_file in config_files:
                    management.copy_files(source=f'{single_config_file}.backup', target=single_config_file)

            management.restart_service()
            ManagementUtils.wait_till_operational(management=management)

        except Exception as restore_backup_exception:
            logger.info(f"Failed to restore {config_files}, Got {restore_backup_exception}")
            assert False, f"Failed to restore {config_files}, Got {restore_backup_exception}"

        finally:
            # validate exeption is raised
            assert False, f'Tried to restore {config_files} because Test failed on exception: \n {original_exception};'
