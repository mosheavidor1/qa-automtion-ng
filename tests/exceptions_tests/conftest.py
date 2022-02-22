from enum import Enum

import pytest


class ExceptionTestType(Enum):
    E2E = 'E2E'
    CREATE_FULL_COVERED_EXCEPTION = "CREATE_FULL_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION = "CREATE_PARTIALLY_COVERED_EXCEPTION"
    EDIT_FULL_COVERED_EXCEPTION = "EDIT_FULL_COVERED_EXCEPTION"
    EDIT_PARTIALLY_COVERED_EXCEPTION = "EDIT_PARTIALLY_COVERED_EXCEPTION"
    CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED = "CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED"


@pytest.fixture(scope="function")
def exception_function_fixture(management, request):
    test_flow = request.param

    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}
    group_name = "empty"

    management.rest_api_client.delete_all_exceptions(timeout=1)
    management.rest_api_client.delete_all_events()
    collector = management.collectors[0]

    collector.create_event(malware_name=malware_name)
    management.rest_api_client.get_security_events({"process": malware_name})

    match test_flow:
        case ExceptionTestType.CREATE_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

            management.rest_api_client.create_group(group_name)
            test_im_params.update({"groups": [group_name]})

            match test_flow:
                case ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
                     ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION:
                    test_im_params.update({"destination": ["IP set"]})

    test_resources = {
        'management': management,
        'collector': collector,
        'create_exception_testim_params': test_im_params,
        'malware_name': malware_name

    }
    yield test_resources

    management.rest_api_client.delete_all_exceptions(timeout=1)
    management.rest_api_client.delete_all_events(timeout=1)

    match test_flow:
        case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

            # that's not good, "Default Collector Group" should be read in the setup section and revert to the value
            # that the test started with
            # TODO - fix it
            management.rest_api_client.move_collector({'ipAddress': collector.os_station.host_ip},
                                                      "Default Collector Group")
