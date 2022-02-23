import time

import allure
import pytest

from infra.assertion.assertion import Assertion, AssertTypeEnum
from infra.system_components.management import Management
from tests.exceptions_tests.conftest import ExceptionTestType


@allure.epic("Management")
@allure.feature("Exception")
class ExceptionsTests:

    @pytest.mark.xray('EN-68879')
    # @pytest.mark.xray('EN-68889')
    @pytest.mark.parametrize('exception_function_fixture',
                             [ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION],
                             indirect=True)
    @pytest.mark.sanity
    def test_create_full_covered_exception(self, exception_function_fixture):
        """
        test name: Full covered exception - event excepted
        steps:
        1. create event DynamicCodeTests
        2. crete exception for DynamicCodeTests
        3. create same event - event should not be created
        """

        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")

        management.rest_api_client.create_exception(event_id)
        management.rest_api_client.delete_all_events()
        collector.create_event(malware_name=malware_name)
        events = management.rest_api_client.get_security_events(validation_data={"process": malware_name},
                                                                timeout=10, fail_on_no_events=False)
        is_event_created = True if len(events) > 0 else False
        Assertion.invoke_assertion(expected=False, actual=is_event_created,
                                   message=f'expected=event not created, actual=event created',
                                   assert_type=AssertTypeEnum.SOFT)


    # @pytest.mark.xray('EN-68890')
    # # @pytest.mark.testim_sanity
    # # Partially covered exception - event excepted
    # def test_create_partially_covered_exception(self, management):
    #     """
    #     steps:
    #     1. create event DynamicCodeTests
    #     2. crete exception for DynamicCodeTests with empty group
    #     3. move collector to the empty group
    #     4. assign group to policies
    #     5. create same event - event should not be created
    #     """
    #     self.test_type = ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION
    #     self.management = management
    #     self.collector = self.management.collectors[0]
    #     self.malware_name = "DynamicCodeTests.exe"
    #     self.play_test()
    #
    # @pytest.mark.xray('EN-68891')
    # # @pytest.mark.testim_sanity
    # # Partially covered exception - event created
    # def test_create_partially_covered_exception_event_created(self, management):
    #     """
    #     steps:
    #     1. create event DynamicCodeTests
    #     2. crete exception for DynamicCodeTests with empty group
    #     3. create same event - event should be created
    #     """
    #     self.test_type = ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED
    #     self.management = management
    #     self.collector = self.management.collectors[0]
    #     self.malware_name = "DynamicCodeTests.exe"
    #     self.play_test()
    #
    # @pytest.mark.xray('EN-68885')
    # # @pytest.mark.testim_sanity
    # def test_edit_fully_covered_exception(self, management):
    #     """
    #     steps:
    #     1. execute test_create_full_covered_exception
    #     2. edit exception - change group to empty group
    #     3. edit exception - change destination to specific destination
    #     """
    #     self.test_type = ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION
    #     self.management = management
    #     self.collector = self.management.collectors[0]
    #     self.malware_name = "DynamicCodeTests.exe"
    #     self.play_test()
    #
    # @pytest.mark.xray('EN-68888')
    # # @pytest.mark.testim_sanity
    # def test_edit_partially_covered_exception(self, management):
    #     """
    #     steps:
    #     1. execute test_create_partially_covered_exception
    #     2. edit exception - change destination to specific destination
    #     """
    #     self.test_type = ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION
    #     self.management = management
    #     self.collector = self.management.collectors[0]
    #     self.malware_name = "DynamicCodeTests.exe"
    #     self.play_test()
    #
    # @pytest.mark.xray('EN-73320')
    # # @pytest.mark.testim_sanity
    # def test_exception_e2e_sanity(self, management):
    #     """
    #     This test run Testim.io to check exceptions
    #     """
    #     self.test_type = ExceptionTestType.E2E
    #     self.management = management
    #     self.collector = self.management.collectors[0]
    #     self.malware_name = "DynamicCodeTests.exe"
    #     self.play_test()
