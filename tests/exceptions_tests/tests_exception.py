import allure
import pytest

from infra.assertion.assertion import Assertion, AssertTypeEnum
from infra.system_components.management import Management
from tests.exceptions_tests.conftest import ExceptionTestType
from tests.utils.management_utils import ManagementUtils
from tests.utils.collector_utils import CollectorUtils


@allure.epic("Management")
@allure.feature("Exception")
class ExceptionsTests:

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [
                                 ('EN-68889', ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION)
                             ],
                             indirect=True)
    @pytest.mark.sanity
    def test_create_full_covered_exception(self, xray, exception_function_fixture):
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
        is_event_created = ManagementUtils.create_excepted_event_and_check(management, collector, malware_name)
        Assertion.invoke_assertion(expected=False, actual=is_event_created,
                                   message=f'expected=event not created, actual=event created',
                                   assert_type=AssertTypeEnum.SOFT)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68890', ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    def test_create_partially_covered_exception(self, xray, exception_function_fixture):
        """
        test name: Partially covered exception - event excepted
        steps:
        1. create event DynamicCodeTests
        2. crete exception for DynamicCodeTests with empty group
        3. move collector to the empty group
        4. assign group to policies
        5. create same event - event should not be created
        """
        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")

        management.rest_api_client.create_exception(event_id, groups=[group_name])
        CollectorUtils.move_collector_and_assign_group_policies(management, collector, group_name)

        is_event_created = ManagementUtils.create_excepted_event_and_check(management, collector, malware_name)
        Assertion.invoke_assertion(expected=False, actual=is_event_created,
                                   message=f'expected=event not created, actual=event created',
                                   assert_type=AssertTypeEnum.SOFT)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68891', ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED)],
                             indirect=True)
    @pytest.mark.sanity
    def test_create_partially_covered_exception_event_created(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. crete exception for DynamicCodeTests with empty group
        3. create same event - event should be created because collector not in the group
        """
        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")

        management.rest_api_client.create_exception(event_id, groups=[group_name])
        is_event_created = ManagementUtils.create_excepted_event_and_check(management, collector, malware_name)
        Assertion.invoke_assertion(expected=True, actual=is_event_created,
                                   message=f'expected=event created, actual=event not created',
                                   assert_type=AssertTypeEnum.SOFT)

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
