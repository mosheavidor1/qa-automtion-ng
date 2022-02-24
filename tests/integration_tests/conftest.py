import pytest


@pytest.fixture(scope='function')
def integration_test_function_fixture(management):

    collector = management.collectors[0]
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {
        "eventName": malware_name,
        "collectorName": str(collector.os_station.host_ip)
    }
    test_resources = {
        'management': management,
        'collector': collector,
        'malware_name': malware_name,
        'test_im_params': test_im_params
    }
    yield test_resources

    management.rest_api_client.delete_event_by_name(malware_name)
