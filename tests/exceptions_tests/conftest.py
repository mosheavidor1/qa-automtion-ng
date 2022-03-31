from enum import Enum
import pytest


class ExceptionTestType(Enum):
    E2E = 'E2E'
    GENERAL = "GENERAL"
    CREATE_FULL_COVERED_EXCEPTION = "CREATE_FULL_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION = "CREATE_PARTIALLY_COVERED_EXCEPTION"
    EDIT_FULL_COVERED_EXCEPTION = "EDIT_FULL_COVERED_EXCEPTION"
    EDIT_PARTIALLY_COVERED_EXCEPTION = "EDIT_PARTIALLY_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED = "CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED"


@pytest.fixture(scope="class", autouse=True)
def setup_method(management):
    # validation if the system is in prevention mode, else turn it on
    policies_names = [management.admin_rest_api_client.rest.NsloPolicies.NSLO_POLICY_EXECUTION_PREVENTION,
                      management.admin_rest_api_client.rest.NsloPolicies.NSLO_POLICY_EXFILTRATION_PREVENTION,
                      management.admin_rest_api_client.rest.NsloPolicies.NSLO_POLICY_RANSOMWARE_PREVENTION]
    policies = management.tenant.rest_api_client.policies.get_policy_info()
    operation_mode = sum([True if policy.get('name') in policies_names and
                                  policy.get('operationMode') == 'Prevention' else False for policy in policies])
    if operation_mode < len(policies_names):
        management.turn_on_prevention_mode()


@pytest.fixture(scope="function")
def exception_function_fixture(management, collector, request):
    test_flow = request.param

    malware_name = "DynamicCodeTests.exe"
    group_name = "empty"
    destination = "Internal Destinations"

    # delete by a given organization name
    management.tenant.rest_api_client.exceptions.delete_all_exceptions(timeout=1)
    management.tenant.rest_api_client.events.delete_all_events()

    start_group = collector.details.collector_group_name

    collector.create_event(malware_name=malware_name)
    events = management.tenant.rest_api_client.events.get_security_events({"process": malware_name})
    event_id = events[0]['eventId']

    match test_flow:
        case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

            management.tenant.rest_api_client.system_inventory.create_group(name=group_name,
                                                                            organization=management.tenant.organization)

    test_resources = {
        'management': management,
        'collector': collector,
        'malware_name': malware_name,
        'event_id': event_id,
        'group_name': group_name,
        'destination': destination

    }
    yield test_resources

    management.tenant.rest_api_client.exceptions.delete_all_exceptions(timeout=1)
    management.tenant.rest_api_client.events.delete_all_events(timeout=1)

    match test_flow:
        case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

            management.tenant.rest_api_client.system_inventory.move_collector(
                validation_data={'ipAddress': collector.os_station.host_ip},
                group_name=start_group)

            match test_flow:
                case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION:
                    test_im_params = {
                        "groupName": [group_name],
                        "loginUser": management.tenant.user_name,
                        "loginPassword": management.tenant.user_password,
                        "loginOrganization": management.tenant.user_password,
                        "organization": management.tenant.organization
                    }
                    management.ui_client.inventory.delete_group(data=test_im_params)
