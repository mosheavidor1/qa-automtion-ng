from enum import Enum
import pytest
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from tests.utils.tenant_utils import generate_group_name

WINDOWS_MALWARE_NAME = "DynamicCodeTests.exe"
LINUX_MALWARE_NAME = "listen"


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
    management.tenant.turn_on_prevention_mode()


@pytest.fixture(scope="function")
def exception_function_fixture(management, collector, request):
    user = management.tenant.default_local_admin
    test_flow = request.param
    malware_name = LINUX_MALWARE_NAME if isinstance(collector, LinuxCollector) else WINDOWS_MALWARE_NAME
    group_name = generate_group_name()
    destination = "Internal Destinations"
    user.rest_components.exceptions.delete_all(safe=True, wait_sec=1)
    user.rest_components.events.delete_all(safe=True)
    rest_collector = user.rest_components.collectors.get_by_ip(ip=collector.host_ip)
    start_group = rest_collector.get_group_name(from_cache=True)
    collector.create_event(malware_name=malware_name)
    events = user.rest_components.events.get_by_process_name(process_name=malware_name, wait_for=True)
    event_id = events[0].id

    match test_flow:
        case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

            if user.rest_components.collector_groups.get_by_name(name=group_name, safe=True) is None:
                user.rest_components.collector_groups.create_collector_group(group_name=group_name)

    test_resources = {
        'management': management,
        'collector': collector,
        'malware_name': malware_name,
        'event_id': event_id,
        'group_name': group_name,
        'destination': destination

    }
    yield test_resources

    user.rest_components.exceptions.delete_all(safe=True, wait_sec=1)
    user.rest_components.events.delete_all(safe=True, wait_sec=1)

    match test_flow:
        case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
             ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
             ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:
            if test_flow == ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION:
                rest_collector.move_to_different_group(target_group_name=start_group)

            match test_flow:
                case ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION | \
                     ExceptionTestType.EDIT_FULL_COVERED_EXCEPTION | \
                     ExceptionTestType.EDIT_PARTIALLY_COVERED_EXCEPTION | \
                     ExceptionTestType.CREATE_PARTIALLY_COVERED_EXCEPTION_EVENT_CREATED:

                    test_im_params = {
                        "groupName": group_name,
                        "loginUser": management.tenant.default_local_admin.get_username(),
                        "loginPassword": management.tenant.default_local_admin.password,
                        "loginOrganization": management.tenant.default_local_admin.password,
                        "organization": management.tenant.organization.get_name()
                    }
                    management.ui_client.inventory.delete_group(data=test_im_params)
