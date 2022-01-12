import allure

from tests.basic_test_lifecycle.base_test import BaseTest


class ExampleFeatureBase(BaseTest):

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        pass

    @allure.step("Reorder environment")
    def cleanup(self):
        pass