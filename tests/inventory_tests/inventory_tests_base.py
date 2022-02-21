from enum import Enum
import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class InventoryTestType(Enum):
    TEST_CHECK_ALL_COMPONENT_APPEAR_AND_RUNNING = 'TEST_CHECK_ALL_COMPONENT_APPEAR_AND_RUNNING'
    TEST_CHECK_COLLECTOR_IS_RUNNING = 'TEST_CHECK_COLLECTOR_IS_RUNNING'
    TEST_EXPORT_PDF_REPORT = 'TEST_EXPORT_PDF_REPORT'
    TEST_EXPORT_EXCEL_REPORT = 'TEST_EXPORT_EXCEL_REPORT'
    TEST_ADD_GROUP = 'TEST_ADD_GROUP'
    TEST_EXPORT_LOGS = 'TEST_EXPORT_LOGS'
    TEST_DELETE_GROP = 'TEST_DELETE_GROP'
    TEST_DISABLED_ENABLED_COLLECTOR = 'TEST_DISABLED_ENABLED_COLLECTOR'
    TEST_MOVE_BETWEEN_ORGANIZATION = 'TEST_MOVE_BETWEEN_ORGANIZATION'


class InventoryTestsBase(BaseTest):
    malware_name = "DynamicCodeTests.exe"
    test_im_params = {"eventName": malware_name}

    test_type: InventoryTestType
    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == InventoryTestType.TEST_CHECK_ALL_COMPONENT_APPEAR_AND_RUNNING:
            self.management.ui_client.inventory.check_components_are_up(data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_CHECK_COLLECTOR_IS_RUNNING:
            self.management.ui_client.inventory.verify_collector_is_running(data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_EXPORT_PDF_REPORT:
            self.management.ui_client.collectors.export_pdf_report(data=self.test_im_params)
            # TODO (yosef) validate that collectors from REST appear in the report

        elif self.test_type == InventoryTestType.TEST_EXPORT_EXCEL_REPORT:
            self.management.ui_client.collectors.export_excel_report(data=self.test_im_params)
            # TODO (yosef) validate that collectors from REST appear in the report

        elif self.test_type == InventoryTestType.TEST_ADD_GROUP:
            self.management.ui_client.collectors.add_group(data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_EXPORT_LOGS:
            self.management.ui_client.collectors.add_group(data=self.test_im_params)
            # TODO: (yosef) validation that folder is not 0 KB

        elif self.test_type == InventoryTestType.TEST_DELETE_GROP:
            self.management.ui_client.inventory.collector_group_deletion_test(data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_DISABLED_ENABLED_COLLECTOR:
            self.management.ui_client.collectors.disabled_and_enabled_collector(data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_MOVE_BETWEEN_ORGANIZATION:
            self.management.ui_client.collectors.move_between_organizations(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        self.management.ui_client.collectors.move_between_organizations(data=self.test_im_params.update({"organizationName": "Default"}))
