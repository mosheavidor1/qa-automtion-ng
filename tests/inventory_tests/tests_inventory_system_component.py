import allure
import pytest
from tests.inventory_tests.inventory_tests_base import InventoryTestsBase,InventoryTestType


@allure.story("Inventory")
class InventorySystemComponentTests(InventoryTestsBase):

    @pytest.mark.xray('EN-73319')
    @pytest.mark.testim_sanity
    def test_check_all_component_appear_and_running(self, management):
        """
        This test run Testim.io for check if collector is running
        """
        self.management = management
        self.test_type = InventoryTestType.TEST_CHECK_ALL_COMPONENT_APPEAR_AND_RUNNING
        self.play_test()
