import allure
import pytest

from infra.system_components.management import Management
from tests.exceptions_tests.conftest import ExceptionTestType
from tests.utils.management_utils import ManagementUtils
from tests.utils.collector_utils import CollectorUtils
from infra.assertion.assertion import AssertTypeEnum, Assertion


@allure.epic("Management")
@allure.feature("Exception")
class ExceptionsTests:

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [
                                 ('EN-68889', ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION)
                             ],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    @pytest.mark.exception
    def test_create_full_covered_exception(self, xray, exception_function_fixture):
        """
        test name: Full covered exception - event excepted
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests
        3. create same event - event should not be created
        """

        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     organization=management.tenant.organization)
        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=False)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68890', ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    def test_create_partially_covered_exception(self, xray, exception_function_fixture):
        """
        test name: Partially covered exception - event excepted
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests with empty group
        3. move collector to the empty group
        4. assign group to policies
        5. create same event - event should not be created
        """
        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     groups=[group_name],
                                                                     organization=management.tenant.organization)
        CollectorUtils.move_collector_and_assign_group_policies(management=management,
                                                                collector=collector,
                                                                group_name=group_name)

        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=False)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68891', ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    def test_create_partially_covered_exception_event_created(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests with empty group
        3. create same event - event should be created because collector not in the group
        """
        management: Management = exception_function_fixture.get('management')
        collector = exception_function_fixture.get('collector')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     groups=[group_name],
                                                                     organization=management.tenant.organization)
        ManagementUtils.create_excepted_event_and_check(management, collector, malware_name, expected_result=True)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68885', ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    @allure.link('http://10.151.100.52/browse/EN-73885')
    def test_edit_fully_covered_exception(self, xray, exception_function_fixture):
        """
        EN-73885 - when fixed add event_id as input to validate_exception
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests
        3. edit exception - change group to empty group
        4. edit exception - change destination to specific destination
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")
        destination = exception_function_fixture.get("destination")
        malware_name = exception_function_fixture.get('malware_name')

        management.rest_api_client.create_exception(event_id)
        management.ui_client.exceptions.edit_exceptions(
            data={"groups": [group_name], "destinations": [destination], "eventID": event_id})
        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     organization=management.tenant.organization)
        test_im_data = {
            "groupName": [group_name],
            "loginUser": management.tenant.user_name,
            "loginPassword": management.tenant.user_password,
            "loginOrganization": management.tenant.user_password,
            "organization": management.tenant.organization,
            "groups": [group_name],
            "destinations": [destination],
            "eventID": event_id
        }
        management.ui_client.exceptions.edit_exceptions(data=test_im_data)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, group=group_name,
                                                          destination=destination)
        assert exception_id, "exception validation failed,exception wasn't created properly"

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68888', ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    @allure.link('http://10.151.100.52/browse/EN-73885')
    def test_edit_partially_covered_exception(self, xray, exception_function_fixture):
        """
        EN-73885 - when fixed add event_id as input to validate_exception
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests with empty group
        3. edit exception - change destination to specific destination
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")
        destination = exception_function_fixture.get("destination")
        malware_name = exception_function_fixture.get('malware_name')

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     groups=[group_name],
                                                                     organization=management.tenant.organization)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, group=group_name)
        assert exception_id, "exception validation failed,exception wasn't created properly"

        test_im_data = {
            "groupName": [group_name],
            "loginUser": management.tenant.user_name,
            "loginPassword": management.tenant.user_password,
            "loginOrganization": management.tenant.user_password,
            "organization": management.tenant.organization,
            "destinations": [destination],
            "eventID": event_id
        }
        management.ui_client.exceptions.edit_exceptions(data=test_im_data)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, group=group_name,
                                                          destination=destination)
        assert exception_id, "exception validation failed,exception wasn't created properly"

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68892', ExceptionTestType.GENERAL)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    def test_delete_exception(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests
        3. remove Exception
        """
        management: Management = exception_function_fixture.get('management')
        malware_name = exception_function_fixture.get('malware_name')
        event_id = exception_function_fixture.get("event_id")

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     organization=management.tenant.organization)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, event_id=event_id)
        assert exception_id, "exception validation failed,exception wasn't created properly"

        management.tenant.rest_api_client.exceptions.delete_exception(exception_id)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, event_id=event_id)
        if exception_id:
            Assertion.invoke_assertion(expected=False, actual=exception_id,
                                       message=r"exception wasn't deleted as expected",
                                       assert_type=AssertTypeEnum.SOFT)

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68992', ExceptionTestType.GENERAL)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    def test_edit_exception_comments(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests
        3. edit exception - change group to empty group
        4. edit exception - add comments
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = exception_function_fixture.get("group_name")
        malware_name = exception_function_fixture.get('malware_name')
        comment = "test edit exception comments"

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     organization=management.tenant.organization)

        testim_data = {
            "groupName": [group_name],
            "loginUser": management.tenant.user_name,
            "loginPassword": management.tenant.user_password,
            "loginOrganization": management.tenant.user_password,
            "organization": management.tenant.organization,
            "groups": [group_name],
            "eventID": event_id,
            "comment": comment
        }
        management.ui_client.exceptions.edit_exceptions(data=testim_data)
        exception_id = ManagementUtils.validate_exception(management, process=malware_name, group=group_name,
                                                          comment=comment)
        assert exception_id, "exception validation failed,exception wasn't created properly"

    @pytest.mark.parametrize('xray, exception_function_fixture',
                             [('EN-68989', ExceptionTestType.GENERAL)],
                             indirect=True)
    @pytest.mark.sanity
    @pytest.mark.management_sanity
    def test_multiple_exceptions(self, xray, exception_function_fixture):
        """
        steps:
        1. create event DynamicCodeTests
        2. create exception for DynamicCodeTests
        3. edit exception - add another exception to the same event
        """
        management: Management = exception_function_fixture.get('management')
        event_id = exception_function_fixture.get("event_id")
        group_name = "Default Collector Group"

        management.admin_rest_api_client.exceptions.create_exception(eventId=event_id,
                                                                     groups=group_name,
                                                                     organization=management.tenant.organization)
        testim_data = {
            "groupName": [group_name],
            "loginUser": management.tenant.user_name,
            "loginPassword": management.tenant.user_password,
            "loginOrganization": management.tenant.user_password,
            "organization": management.tenant.organization
        }
        management.ui_client.exceptions.add_another_exception(data=testim_data)
        exception_id = ManagementUtils.validate_exception(management, event_id=event_id, group=group_name)
        assert exception_id, "exception validation failed,exception wasn't created properly"
        exception_id_2 = ManagementUtils.validate_exception(management, event_id=event_id)
        assert exception_id_2, "exception validation failed,exception wasn't created properly"

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
