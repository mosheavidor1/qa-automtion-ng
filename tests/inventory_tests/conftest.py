import pytest


@pytest.fixture(scope='function')
def inventory_function_fixture(management):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_resources = {
        'management': management,
        'test_im_params': test_im_params
    }
    yield test_resources

    management.ui_client.collectors.move_between_organizations(data=test_im_params.update({"organizationName": "Default"}))
