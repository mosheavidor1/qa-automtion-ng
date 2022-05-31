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
        management.tenant.rest_api_client.events.delete_all_events()
        collector.create_event(malware_name=malware_name)
        events = management.tenant.rest_api_client.events.get_security_events(validation_data={"process": malware_name},
                                                                              timeout=10, fail_on_no_events=False)
        is_event_created = True if len(events) > 0 else False
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
