import pytest


@pytest.fixture(scope='function')
def dynamic_content_function_fixture(management):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"secUserName": "FortiEDRAdmin",
                      "secUserTitle": "local admin",
                      "secUserFirstName": "first admin",
                      "secUserLastName": "last admin",
                      "secUserEmail": "FortiEDRAdmin@fortinet.com",
                      "secUserPassword": "12345678",
                      "secUserRules": ["Rest API", "Admin", "Local Admin"],
                      "eventName": malware_name}

    collector = management.collectors[0]

    management.rest_api_client.delete_events()
    management.rest_api_client.delete_all_exceptions()

    test_resources = {
        'management': management,
        'collector': collector,
        'test_im_params': test_im_params,
        'malware_name': malware_name
    }
    yield test_resources

    management.rest_api_client.delete_event_by_name(malware_name)
