import allure
import pytest


@allure.epic("Management")
@allure.feature("Inventory")
class InventorySystemComponentTests:

    @pytest.mark.xray('EN-73319')
    def test_check_all_component_appear_and_running(self, inventory_function_fixture):
        """
        This test run Testim.io for check if collector is running
        """
        management = inventory_function_fixture.get('management')
        test_im_params = inventory_function_fixture.get('test_im_params')
        management.ui_client.inventory.check_components_are_up(data=test_im_params)
