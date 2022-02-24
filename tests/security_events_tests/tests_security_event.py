import allure
import pytest


@allure.epic("Management")
@allure.feature("Security Events")
class SecurityEventTests:

    @pytest.mark.xray('EN-73626')
    def test_security_event_export_excel_report(self, security_events_function_fixture):
        """
        This test run Testim.io for export Excel report from event viewer page
        """
        management = security_events_function_fixture.get('management')
        test_im_params = security_events_function_fixture.get('test_im_params')
        management.ui_client.security_events.export_excel_report(data=test_im_params)

    @pytest.mark.xray('EN-73627')
    def test_security_event_export_PDF_report(self, security_events_function_fixture):
        """
        This test run Testim.io for export PDF report from event viewer page
        """
        management = security_events_function_fixture.get('management')
        test_im_params = security_events_function_fixture.get('test_im_params')
        management.ui_client.security_events.export_pdf_report(data=test_im_params)