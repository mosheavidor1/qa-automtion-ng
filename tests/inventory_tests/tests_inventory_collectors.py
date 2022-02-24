import allure
import pytest


@allure.epic("Management")
@allure.feature("Inventory")
class InventoryCollectorsTests:

    @pytest.mark.xray('EN-73621')
    def test_check_collector_is_running(self, inventory_function_fixture):
        """
        This test use Testim.io to check if the collector is running
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.inventory.verify_collector_is_running(data=test_im_params)

    @pytest.mark.xray('EN-73324')
    def test_export_PDF_report(self, inventory_function_fixture):
        """
        This test use Testim.io to check export of PDF report
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.export_pdf_report(data=test_im_params)
        # TODO (yosef) validate that collectors from REST appear in the report

    @pytest.mark.xray('EN-73325')
    def test_export_EXCEL_report(self, inventory_function_fixture):
        """
        This test use Testim.io to check export of EXCEL report
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.export_excel_report(data=test_im_params)
        # TODO (yosef) validate that collectors from REST appear in the report

    @pytest.mark.xray('EN-73313')
    def test_add_group(self, inventory_function_fixture):
        """
        This test use Testim.io to check adding group
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.add_group(data=test_im_params)

    @pytest.mark.xray('EN-73321')
    def test_export_logs(self, inventory_function_fixture):
        """
        This test use Testim.io for export collector logs
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.add_group(data=test_im_params)
        # TODO: (yosef) validation that folder is not 0 KB

    @pytest.mark.xray('EN-73307')
    def test_delete_grop(self, inventory_function_fixture):
        """
        This test use Testim.io for delete grup with and without the collector in the group
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.inventory.collector_group_deletion_test(data=test_im_params)

    @pytest.mark.xray('EN-73623')
    def test_disabled_enabled_collector(self, inventory_function_fixture):
        """
        This test use Testim.io for change mode of collector to disabled and enabled
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.disabled_and_enabled_collector(data=test_im_params)

    @pytest.mark.xray('EN-73323')
    def test_move_between_organization(self, inventory_function_fixture):
        """
        This test use Testim.io for change mode of collector to disabled and enabled
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.collectors.move_between_organizations(data=test_im_params)
