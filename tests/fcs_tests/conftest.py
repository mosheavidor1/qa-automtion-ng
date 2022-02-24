import pytest


@pytest.fixture(scope="function")
def fcs_tests_function_fixture(management):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    collector = management.collectors[0]

    management.rest_api_client.delete_events()
    management.rest_api_client.delete_all_exceptions()

    collector.create_event(malware_name=malware_name)
    management.rest_api_client.get_security_events({"process": malware_name})

    test_resources = {
        'management': management,
        'test_im_params': test_im_params
    }

    yield test_resources

    management.rest_api_client.delete_event_by_name(malware_name)
