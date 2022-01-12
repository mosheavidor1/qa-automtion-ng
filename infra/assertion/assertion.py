from enum import Enum

import allure

from infra.allure_report_handler.reporter import Reporter


class AssertTypeEnum(Enum):
    SOFT = 'SOFT'
    HARD = 'HARD'


class Assertion:
    fails_list = []

    @staticmethod
    def invoke_assertion(expected,
                         actual,
                         message: str,
                         assert_type: AssertTypeEnum.HARD):

        if expected != actual:
            if assert_type == AssertTypeEnum.SOFT:
                Assertion.fails_list.append(message)

            elif assert_type == AssertTypeEnum.HARD:
                assert False, message

            else:
                raise Exception(f'Unknown assertion type: {assert_type}')

    @staticmethod
    @allure.step("Checking if soft asserts collected during the test")
    def assert_all():
        if len(Assertion.fails_list) > 0:
            for single_message in Assertion.fails_list:
                Reporter.report(single_message)

            Assertion.fails_list.clear()
            assert False, "Test failed due to soft asserts that was collected during the test"


