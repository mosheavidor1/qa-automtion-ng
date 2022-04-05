import time

import allure
import pytest

from infra.system_components.management import Management


@allure.epic("Management")
@allure.feature("Dynamic content")
class DynamicContentTests:

    @pytest.mark.xray('EN-73362')
    def test_e2e_exception_dynamic_content(self, dynamic_content_function_fixture):
        """
        This test run Testim.io for check dynamic content exception
        """
        management: Management = dynamic_content_function_fixture.get('management')
        collector = dynamic_content_function_fixture.get('collector')
        malware_name = dynamic_content_function_fixture.get('malware_name')
        test_im_params = dynamic_content_function_fixture.get('test_im_params')

        collector.create_event(malware_name=malware_name)
        management.tenant.rest_api_client.events.get_security_events({"process": malware_name})
        management.ui_client.security_events.search_event(data=test_im_params)
        management.ui_client.dynamic_content.add_exception(data=test_im_params)
        management.tenant.rest_api_client.events.delete_all_events()
        collector.create_event(malware_name=malware_name)
        management.ui_client.security_events.event_does_not_appear(data=test_im_params)