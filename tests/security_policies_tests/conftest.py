import pytest


@pytest.fixture(scope="function")
def security_events_function_fixture(management, collector):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {
        "loginUser": management.tenant.default_local_admin.get_username(),
        "loginPassword": management.tenant.default_local_admin.password,
        "loginOrganization": management.tenant.organization.get_name(),
        "organization": management.tenant.organization.get_name(),
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