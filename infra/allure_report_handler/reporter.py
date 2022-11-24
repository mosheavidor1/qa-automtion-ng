import logging

import allure


_logger = logging.getLogger('TEST_STEP')


def _step(message):
    """
    1. Logs test case (allure step) msg to debug log and to Allure report.
    2. Triggering Allure step context.
    """
    _logger.info(message)
    return allure.step(message)


INFO = _logger.info
TEST_STEP = _step


class Reporter:

    @staticmethod
    def report(message: str, logger_func=None):
        if logger_func is not None:
            logger_func(message)
        with allure.step(message):
            pass

    @staticmethod
    def allure_step_context(message: str, logger_func):
        logger_func(message)
        return allure.step(message)

    @staticmethod
    def step(message: str, is_failed: bool):
        with allure.step(message):
            assert is_failed, message

    @staticmethod
    def attach_screenshot(driver, screenshot_name):
        allure.attach(driver.get_screenshot_as_png(), name=screenshot_name, attachment_type=allure.attachment_type.PNG)

    @staticmethod
    def attach_str_as_file(file_name: str, file_content: str):
        allure.attach(name=file_name, body=file_content, attachment_type=allure.attachment_type.TEXT)

    @staticmethod
    def attach_str_as_json_file(file_name: str, file_content: str):
        allure.attach(name=file_name, body=file_content, attachment_type=allure.attachment_type.JSON)
