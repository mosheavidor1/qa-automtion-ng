import pytest


@pytest.fixture(scope="function")
def security_events_function_fixture(management):
    malware_name = "DynamicCodeTests.exe"
    collector = management.collectors[0]
    test_im_params = {
        "eventName": malware_name,
        "collectorName": str(collector.os_station.get_hostname())
    }
    management.ui_client.exceptions.delete_all_exceptions(data=test_im_params)
    test_resources = {
        'management': management,
        'malware_name': malware_name,
        'collector': collector,

    }
    yield test_resources

    management.rest_api_client.delete_event_by_name(malware_name)
    management.ui_client.security_policies.set_policies({"securityPolicyMode": "Prevention"})