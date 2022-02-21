import allure
import pytest
from tests.audit_tests.audit_tests_base import AuditTestsBase


@allure.epic("Management")
@allure.feature("Audit")
# @pytest.mark.sanity
class AuditTests(AuditTestsBase):

    @pytest.mark.xray('EN-73328')
    # @pytest.mark.testim_sanity
    def test_audit(self, management):
        """
        This test run Testim.io to create Audit report
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.play_test()



