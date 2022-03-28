import pytest


@pytest.fixture(scope="function")
def security_events_function_fixture(management, collector):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {
        "eventName": malware_name,
        "collectorName": str(collector.os_station.get_hostname())
    }
    management.admin_rest_api_client.exceptions.delete_all_exceptions()
    test_resources = {
        'management': management,
        'malware_name': malware_name,
        'collector': collector,

    }
    yield test_resources

    management.admin_rest_api_client.events.delete_event_by_name(malware_name)
    management.ui_client.security_policies.set_policies({"securityPolicyMode": "Prevention"})