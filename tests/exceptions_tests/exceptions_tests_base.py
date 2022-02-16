import allure
from enum import Enum


from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import Assertion, AssertTypeEnum
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler
from time import sleep


class ExceptionTestType(Enum):
    E2E = 'E2E'
    CREATE_FULL_COVERED_EXCEPTION = "CREATE_FULL_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION = "CREATE_PARTIALLY_COVERED_EXCEPTION"
    EDIT_FULL_COVERED_EXCEPTION = "EDIT_FULL_COVERED_EXCEPTION"
    EDIT_PARTIALLY_COVERED_EXCEPTION = "EDIT_PARTIALLY_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED = "CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED"


class ExceptionsTestsBase(BaseTest):
    test_type: ExceptionTestType = ExceptionTestType.E2E
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}
    group_name = "empty"

    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        Reporter.report("create event")

        self.management.rest_ui_client.delete_all_exceptions(timeout=1)
        self.management.rest_ui_client.delete_all_events()
        self.collector.create_event(malware_name=self.malware_name)

        self.management.rest_ui_client.get_security_events({"process": self.malware_name})

        if self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
            self.management.rest_ui_client.create_group(self.group_name)
            self.test_im_params.update({"groupName": [self.group_name]})

            if self.test_type == ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION or\
                    self.test_type == ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION:
                self.test_im_params.update({"destination": ["IP set"]})

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION:
            self.create_full_covered_exception()

        elif self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
            self.create_partially_covered_exception()

        elif self.test_type == ExceptionTestType.E2E:
            self.exception_e2e_sanity()

        if self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION:
            self.management.rest_ui_client.move_collector({'ipAddress': self.collector.os_station.host_ip},
                                                          self.group_name)
            self.management.rest_ui_client.assign_policy('Exfiltration Prevention', self.group_name, timeout=1)
            self.management.rest_ui_client.assign_policy('Execution Prevention', self.group_name, timeout=1)
            self.management.rest_ui_client.assign_policy('Ransomware Prevention', self.group_name)

        if self.test_type == ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION or \
                self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
            event_created = self.create_excepted_event_and_check()
            if self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
                Assertion.invoke_assertion(expected=True, actual=event_created,
                                           message=f'expected=event created, actual=event not created',
                                           assert_type=AssertTypeEnum.SOFT)

            else:
                Assertion.invoke_assertion(expected=False, actual=event_created,
                                           message=f'expected=event not created, actual=event created',
                                           assert_type=AssertTypeEnum.SOFT)

        elif self.test_type == ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION or\
                self.test_type == ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION:
            self.edit_covered_exception()

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.rest_ui_client.delete_all_exceptions(timeout=1)
        self.management.rest_ui_client.delete_all_events(timeout=1)
        if self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION or \
                self.test_type == ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION or \
                self.test_type == ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION or \
                self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
            self.management.rest_ui_client.move_collector({'ipAddress': self.collector.os_station.host_ip},
                                                          "Default Collector Group")
        if self.test_type == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION:
            test_name = "Collectors | Delete group"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

    def exception_e2e_sanity(self):
        self.delete_and_archive()

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Search event"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        self.delete_and_archive()

        self.collector.create_event(malware_name=self.malware_name)

        test_name = "Security event | Search event"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        test_name = "Exceptions | Create exception"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

        self.management.rest_ui_client.delete_all_events()

        sleep(30)
        self.create_excepted_event_and_check()

    def delete_and_archive(self):
        self.management.rest_ui_client.delete_all_exceptions()

        self.management.rest_ui_client.delete_all_events()

    def create_excepted_event_and_check(self):
        self.management.rest_ui_client.delete_all_events()

        sleep(30)

        self.collector.create_event(malware_name=self.malware_name)

        events = self.management.rest_ui_client.get_security_events(validation_data={"process": self.malware_name},
                                                                    timeout=10, fail_on_no_events=False)
        if len(events) > 0:
            return True
        else:
            return False

    def create_full_covered_exception(self):
        test_name = "Exceptions | Create exception"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    def create_partially_covered_exception(self):
        test_name = "Exceptions | Create exception"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

    def edit_covered_exception(self):
        test_name = "Edit group"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)
        test_name = "Edit destination"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params)

