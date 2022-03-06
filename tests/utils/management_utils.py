import allure
from infra.system_components.collector import Collector
from infra.system_components.management import Management
from infra.assertion.assertion import Assertion, AssertTypeEnum


class ManagementUtils:

    @staticmethod
    @allure.step("create excepted event and check if created")
    def create_excepted_event_and_check(management: Management, collector: Collector, malware_name, expected_result):
        """
        create event with existing exception and check if created
        """
        management.rest_api_client.delete_all_events()
        collector.create_event(malware_name=malware_name)
        events = management.rest_api_client.get_security_events(validation_data={"process": malware_name},
                                                                timeout=10, fail_on_no_events=False)
        is_event_created = True if len(events) > 0 else False
        Assertion.invoke_assertion(expected=expected_result, actual=is_event_created,
                                   message=r"event was\wasn't created as expected",
                                   assert_type=AssertTypeEnum.SOFT)

    @staticmethod
    @allure.step("validate exception exists with given parameters")
    def validate_exception(management, process, event_id=None, group='All Collector Groups',
                           destination='All Destinations', user='All Users'):
        exceptions = management.rest_api_client.get_exceptions(event_id)
        for exception in exceptions:
            if process in str(exception) and \
                    group in exception['selectedCollectorGroups'] and \
                    destination in exception['selectedDestinations'] and \
                    user in exception['selectedUsers']:
                return exception['exceptionId']
        return False
