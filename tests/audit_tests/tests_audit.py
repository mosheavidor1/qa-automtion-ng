import allure
import pytest


@allure.epic("Management")
@allure.feature("Audit")
@pytest.mark.sanity
class AuditTests:

    @pytest.mark.xray('EN-73328')
    def test_verify_audit_file_was_downloaded(self, management):
        """
        1. Login
        2. go to Administrator > Tools page
        3. In the Audit trail, insert start data from 30 days ago and until to today
        4. click on generate audit button
        5. Verify that file was downloaded
        """
        malware_name = "DynamicCodeTests.exe"
        test_im_params = {"eventName": malware_name}
        management.ui_client.audit.export_report(test_im_params)



