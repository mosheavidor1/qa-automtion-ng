import pytest


@pytest.fixture(scope='function')
def system_events_function_fixture(management, collector):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    collector.create_event(malware_name=malware_name)
    management.admin_rest_api_client.events.get_security_events({"process": malware_name})

    test_resources = {
        'management': management,
        'test_im_params': test_im_params
    }
    yield test_resources

    management.admin_rest_api_client.events.delete_event_by_name(malware_name)