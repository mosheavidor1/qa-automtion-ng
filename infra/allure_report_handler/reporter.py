import allure


class Reporter:

    @staticmethod
    def report(message: str):
        with allure.step(message):
            pass

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
