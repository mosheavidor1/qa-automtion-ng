import allure
import pytest
from infra.system_components.collector import Collector
from tests.security_policies_tests.security_policies_tests_base import ExceptionsTestsBase


@allure.epic("Management")
@allure.feature("Security policies")
class SecurityPoliciesTests(ExceptionsTestsBase):
    collector: Collector = None

    @pytest.mark.xray('EN-73632')
    @pytest.mark.testim_sanity
    def test_security_policies_simulation_mode(self, management):
        """
        This test run Testim.io for check system in simulation mode
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.malware_name = "DynamicCodeTests.exe"
        self.play_test()

