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
     1.Login
        2.go to security settings - Exclusion Manger
        3.Add list
        4.Rename list
        5.Add exclusion file
        6.Trigger file from collector
        7.Check that file is excluded
        8.Delete file
        9.Check that file is no longer excluded
        10.delete list
        11.Logout
        """
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.audit.export_report(test_im_params)
