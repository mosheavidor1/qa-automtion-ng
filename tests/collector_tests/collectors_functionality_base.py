from enum import Enum

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import Assertion, AssertTypeEnum
from infra.enums import SystemState
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class CollectorFunctionalityTestType(Enum):
    STOP_START_COLLECTOR = 'STOP_START_COLLECTOR'
    STOP_COLLECTOR_CHECK_IS_UP_FAIL_ON_PURPOSE = 'STOP_COLLECTOR_CHECK_IS_UP_FAIL_ON_PURPOSE'
    CREATE_FAKE_DUMP_FILE = 'CREATE_FAKE_DUMP_FILE'
    TEST_WITH_SOFT_ASSERT = 'TEST_WITH_SOFT_ASSERT'


class CollectorsTestsBase(BaseTest):

    test_type: CollectorFunctionalityTestType = CollectorFunctionalityTestType.STOP_START_COLLECTOR
    crash_folder_path = r"C:\ProgramData\FortiEdr\CrashDumps\Collector"
    crash_file_name = "crash_dumps_info.txt"
    testim_handler: TestImHandler = TestImHandler()
    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):

        if self.test_type == CollectorFunctionalityTestType.STOP_START_COLLECTOR or\
                self.test_type == CollectorFunctionalityTestType.STOP_COLLECTOR_CHECK_IS_UP_FAIL_ON_PURPOSE:

            Reporter.report("Check if collector service is running before test")
            self.management.collectors[0].validate_collector_is_up_and_running(timeout=0)

        elif self.test_type == CollectorFunctionalityTestType.CREATE_FAKE_DUMP_FILE:
            self.management.collectors[0].os_station.copy_files(source='C:\CrashDumpsCollected\*', target='C:\Windows\crashdumps')
            self.management.collectors[0].os_station.create_new_folder(folder_path=self.crash_folder_path)
            self.management.collectors[0].os_station.execute_cmd(
                cmd=rf'echo "This is a dummy crash file with dummy content" > {self.crash_folder_path}\{self.crash_file_name} ')

    @allure.step("Run and validate")
    def run_and_validate(self):
        if self.test_type == CollectorFunctionalityTestType.STOP_COLLECTOR_CHECK_IS_UP_FAIL_ON_PURPOSE:
            self.management.collectors[0].stop_collector(password='12345678')
            self.management.collectors[0].validate_collector_is_up_and_running()

        elif self.test_type == CollectorFunctionalityTestType.CREATE_FAKE_DUMP_FILE:
            is_file_exist = self.management.collectors[0].os_station.is_path_exist(path=rf'{self.crash_folder_path}\{self.crash_file_name}')
            if is_file_exist:
                Reporter.report("The crash file exist :) - just a print")

        elif self.test_type == CollectorFunctionalityTestType.TEST_WITH_SOFT_ASSERT:
            Reporter.report('Going to add soft assert')
            Assertion.invoke_assertion(expected='fake_expected', actual='fake_actual', message=f'expected is not equal to actual: expected="fake_expected", actual="fake_actual"', assert_type=AssertTypeEnum.SOFT)
            Reporter.report("Test continue although soft assert was added")
            self.collector.get_collector_status()

    @allure.step("Validate that test didn't damage the environment")
    def cleanup(self):
        self.management.collectors[0].validate_collector_is_up_and_running(timeout=0)
