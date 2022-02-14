from enum import Enum
import allure
from infra.allure_report_handler.reporter import Reporter
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


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
    testim_handler: TestImHandler = TestImHandler()

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == InventoryTestType.TEST_CHECK_ALL_COMPONENT_APPEAR_AND_RUNNING:
            test_name = "Inventory | check components running"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_CHECK_COLLECTOR_IS_RUNNING:
            test_name = "Inventory | Verify Collector is Running"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_EXPORT_PDF_REPORT:
            test_name = "collectors | export PDF report"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)
            # TODO (yosef) validate that collectors from REST appear in the report

        elif self.test_type == InventoryTestType.TEST_EXPORT_EXCEL_REPORT:
            test_name = "collectors | export EXCEL report"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)
            # TODO (yosef) validate that collectors from REST appear in the report

        elif self.test_type == InventoryTestType.TEST_ADD_GROUP:
            test_name = "Collectors | Add group"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_EXPORT_LOGS:
            test_name = "Collectors | Add group"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)
            # TODO: (yosef) validation that folder is not 0 KB

        elif self.test_type == InventoryTestType.TEST_DELETE_GROP:
            test_name = "Inventory | Collector Group deletion tests"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_DISABLED_ENABLED_COLLECTOR:
            test_name = "Collectors | disabled and enabled collector"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

        elif self.test_type == InventoryTestType.TEST_MOVE_BETWEEN_ORGANIZATION:
            test_name = "Collectors | Move between organization"
            self.testim_handler.run_test(test_name=test_name,
                                         ui_ip=self.management.host_ip,
                                         data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        test_name = "Collectors | Move between organization"
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=self.management.host_ip,
                                     data=self.test_im_params.update({"organizationName": "Default"}))
