import allure
import pytest


@allure.epic("Management")
@allure.feature("FCS")
class FcsTests:

    @pytest.mark.xray('EN-73353')
    def test_vulnerability_on_application(self, fcs_tests_function_fixture):
        """
        This test run Testim.io for check CVE (Vulnerability)
        """
        management = fcs_tests_function_fixture.get('management')
        test_im_params = fcs_tests_function_fixture.get('test_im_params')

        # TODO:(yosef) run aplication with CVE from collector
        management.ui_client.fcs.validate_connection_to_fcs_by_vulnerability(data=test_im_params)

    @pytest.mark.xray('EN-73352')
    def test_reclassification_on_security_event(self, fcs_tests_function_fixture):
        """
        This test run Testim.io for check Reclassification
        """
        management = fcs_tests_function_fixture.get('management')
        test_im_params = fcs_tests_function_fixture.get('test_im_params')

        management.ui_client.fcs.validate_connection_to_fcs_by_reclassification(data=test_im_params)
