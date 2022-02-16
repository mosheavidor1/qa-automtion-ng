import allure
import pytest

from tests.inventory_tests.inventory_tests_base import InventoryTestsBase, InventoryTestType


@allure.epic("Management")
@allure.feature("Inventory")
class InventoryCollectorsTests(InventoryTestsBase):

    @pytest.mark.xray('EN-73621')
    @pytest.mark.testim_sanity
    def test_check_collector_is_running(self, management):
        """
        This test use Testim.io to check if the collector is running
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_CHECK_COLLECTOR_IS_RUNNING
        self.play_test()

    @pytest.mark.xray('EN-73324')
    @pytest.mark.testim_sanity
    def test_export_PDF_report(self, management):
        """
        This test use Testim.io to check export of PDF report
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_EXPORT_PDF_REPORT
        self.play_test()

    @pytest.mark.xray('EN-73325')
    @pytest.mark.testim_sanity
    def test_export_EXCEL_report(self, management):
        """
        This test use Testim.io to check export of EXCEL report
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_EXPORT_EXCEL_REPORT
        self.play_test()

    @pytest.mark.xray('EN-73313')
    @pytest.mark.testim_sanity
    def test_add_group(self, management):
        """
        This test use Testim.io to check adding group
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_ADD_GROUP
        self.play_test()

    @pytest.mark.xray('EN-73321')
    @pytest.mark.testim_sanity
    def test_export_logs(self, management):
        """
        This test use Testim.io for export collector logs
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_EXPORT_LOGS
        self.play_test()

    @pytest.mark.xray('EN-73307')
    @pytest.mark.testim_sanity
    def test_delete_grop(self, management):
        """
        This test use Testim.io for delete grup with and without the collector in the group
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_DELETE_GROP
        self.play_test()

    @pytest.mark.xray('EN-73623')
    @pytest.mark.testim_sanity
    def test_disabled_enabled_collector(self, management):
        """
        This test use Testim.io for change mode of collector to disabled and enabled
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_DISABLED_ENABLED_COLLECTOR
        self.play_test()

    @pytest.mark.xray('EN-73323')
    @pytest.mark.testim_sanity
    def test_move_between_organization(self, management):
        """
        This test use Testim.io for change mode of collector to disabled and enabled
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_MOVE_BETWEEN_ORGANIZATION
        self.play_test()
