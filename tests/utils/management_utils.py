import time
import allure
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.assertion.assertion import Assertion, AssertTypeEnum


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
        exceptions = management.tenant.rest_api_client.exceptions.get_exceptions(event_id)
        for exception in exceptions:
            if process in str(exception) and \
                    group in exception['selectedCollectorGroups'] and \
                    destination in exception['selectedDestinations'] and \
                    user in exception['selectedUsers'] and \
                    (comment is None or comment in exception['comment']):
                return exception['exceptionId']
        return False
