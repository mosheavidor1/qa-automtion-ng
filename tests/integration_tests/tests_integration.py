import allure
import pytest


@allure.epic("Management")
@allure.feature("Integration")
class IntegrationTests:

    @pytest.mark.xray('EN-73334')
    def test_custom_connector(self, integration_test_function_fixture):
        """
        This test run Testim.io for check creating of custom connector and configure the playbook
        and trigger event from Collector for check the enforcement
        """
        management = integration_test_function_fixture.get('management')
        collector = integration_test_function_fixture.get('collector')
        test_im_params = integration_test_function_fixture.get('test_im_params')
        malware_name = integration_test_function_fixture.get('malware_name')

        management.ui_client.connectors.create_custom_connector(data=test_im_params)
        collector.create_event(malware_name=malware_name)
        management.ui_client.security_events.search_archived_event(data=test_im_params)
        management.ui_client.connectors.check_custom_connector_enforcement(data=test_im_params)
