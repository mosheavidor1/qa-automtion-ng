import allure
import pytest
from tests.audit_tests.audit_tests_base import AuditTestsBase


@allure.epic("Management")
@allure.feature("Audit")
@pytest.mark.sanity
class AuditTests(AuditTestsBase):

    @pytest.mark.xray('EN-73328')
    def test_verify_audit_file_was_downloaded(self, management):
        """
        1. Login
        2. go to Administrator > Tools page
        3. In the Audit trail, insert start data from 30 days ago and until to today
        4. click on generate audit button
        5. Verify that file was downloaded
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.play_test()



