import allure
import pytest
from tests.integration_tests.integration_tests_base import IntegrationTestsBase


@allure.epic("Management")
@allure.feature("Integration")
class IntegrationTests(IntegrationTestsBase):

    @pytest.mark.xray('EN-73334')
    #@pytest.mark.testim_sanity
    def test_custom_connector(self, management):
        """
        This test run Testim.io for check creating of custom connector and configure the playbook
        and trigger event from Collector for check the enforcement
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": str(self.collector.os_station.host_ip)
        }
        self.play_test()
