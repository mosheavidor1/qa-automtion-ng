import allure
import pytest
from infra.system_components.collector import CollectorAgent


@allure.epic("Management")
@allure.feature("Security policies")
class SecurityPoliciesTests:
    collector: CollectorAgent = None

    @pytest.mark.xray('EN-73632')
    def test_security_policies_simulation_mode(self, security_events_function_fixture):
        """
        This test run Testim.io for check system in simulation mode
        """
        management = security_events_function_fixture.get('management')
        test_im_params = security_events_function_fixture.get('test_im_params')
        malware_name = security_events_function_fixture.get('malware_name')
        collector = security_events_function_fixture.get('collector')

        management.ui_client.security_policies.set_policies(data=test_im_params.update({"securityPolicyMode": "Simulation"}))
        management.ui_client.security_events.archive_all()
        collector.create_event(malware_name=malware_name)
        management.ui_client.security_events.check_if_event_in_simulation_block_mode(data=test_im_params)

