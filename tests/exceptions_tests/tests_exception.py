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
        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=False)

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

        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=False)

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
        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=True)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68885', ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    def test_edit_fully_covered_exception(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. crete exception for DynamicCodeTests
        3. edit exception - change group to empty group
        4. edit exception - change destination to specific destination
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")
        destination = exception_function_fixture.get("destination")

        management.rest_api_client.create_exception(event_id)

        management.ui_client.exceptions.edit_exceptions({"groups": [group_name]})

        management.ui_client.exceptions.edit_exceptions({"destination": [destination]})

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68888', ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    def test_edit_partially_covered_exception(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. crete exception for DynamicCodeTests with empty group
        3. edit exception - change destination to specific destination
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")
        destination = exception_function_fixture.get("destination")

        management.rest_api_client.create_exception(event_id, groups=[group_name])

        management.ui_client.exceptions.edit_exceptions({"destination": [destination]})

    # @pytest.mark.xray('EN-73320')
    # # @pytest.mark.testim_sanity
    # def test_exception_e2e_sanity(self, management):
    #     """
    #     This test run Testim.io to check exceptions
    #     """
    # self.delete_and_archive()
    #
    # self.collector.create_event(malware_name=self.malware_name)
    #
    # self.management.ui_client.security_events.search_event(data=self.test_im_params)
    #
    # self.management.rest_api_client.delete_all_exceptions()
    #
    # self.management.rest_api_client.delete_all_events()
    #
    # self.collector.create_event(malware_name=self.malware_name)
    #
    # self.management.ui_client.security_events.search_event(data=self.test_im_params)
    #
    # self.management.ui_client.exceptions.create_exception(data=self.test_im_params)
    #
    # self.management.rest_api_client.delete_all_events()
    #
    # self.create_excepted_event_and_check()