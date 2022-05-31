import allure
import pytest


@allure.epic("Management")
@allure.feature("Audit")
@pytest.mark.sanity
@pytest.mark.management_sanity
class AuditTests:

    @pytest.mark.xray('EN-73328')
    def test_verify_audit_file_was_downloaded(self, management, collector):
        """
        1. Login
        2. go to Administrator > Tools page
        3. In the Audit trail, insert start data from 30 days ago and until to today
        4. click on generate audit button
        5. Verify that file was downloaded
        """
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.audit.export_report(test_im_params)
