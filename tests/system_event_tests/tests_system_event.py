import allure
import pytest


@allure.epic("Management")
@allure.feature("System event")
class SystemEventTests:

    @pytest.mark.xray('EN-73349')
    def test_export_PDF_report(self, system_events_function_fixture):
        """
        This test run Testim.io for check export PDF report from System event page
        """
        management = system_events_function_fixture.get('management')
        test_im_params = system_events_function_fixture.get('test_im_params')

        management.ui_client.system_events.export_pdf_report(test_im_params)

    @pytest.mark.xray('EN-73327')
    def test_events_of_prevention_and_simulation(self, system_events_function_fixture):
        """
        This test run Testim.io for check that changed mode to simulation or prevention is recorded in system event
        """
        management = system_events_function_fixture.get('management')
        test_im_params = system_events_function_fixture.get('test_im_params')
        management.ui_client.system_events.prevention_simulation(test_im_params)