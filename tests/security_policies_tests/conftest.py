import pytest


@pytest.fixture(scope="function")
def security_events_function_fixture(management, collector):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {
        "loginUser": management.tenant.user_name,
        "loginPassword": management.tenant.user_password,
        "loginOrganization": management.tenant.organization,
        "organization": management.tenant.organization,
        "eventName": malware_name,
        "collectorName": str(collector.os_station.get_hostname())
    }
    management.tenant.rest_api_client.exceptions.delete_all_exceptions()
    test_resources = {
        'management': management,
        'malware_name': malware_name,
        'collector': collector,
        'test_im_params': test_im_params
    }
    yield test_resources

    management.tenant.rest_api_client.events.delete_event_by_name(malware_name)

    test_im_params.update({"securityPolicyMode": "Prevention"})
    management.ui_client.security_policies.set_policies(test_im_params)