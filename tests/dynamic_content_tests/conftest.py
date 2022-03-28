import pytest


@pytest.fixture(scope='function')
def dynamic_content_function_fixture(management, collector):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"secUserName": "FortiEDRAdmin",
                      "secUserTitle": "local admin",
                      "secUserFirstName": "first admin",
                      "secUserLastName": "last admin",
                      "secUserEmail": "FortiEDRAdmin@fortinet.com",
                      "secUserPassword": "12345678",
                      "secUserRules": ["Rest API", "Admin", "Local Admin"],
                      "eventName": malware_name}

    management.admin_rest_api_client.events.delete_events()
    management.admin_rest_api_client.events.delete_all_exceptions()

    test_resources = {
        'management': management,
        'collector': collector,
        'test_im_params': test_im_params,
        'malware_name': malware_name
    }
    yield test_resources

    management.admin_rest_api_client.events.delete_event_by_name(malware_name)
