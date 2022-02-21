import allure

from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest
from infra.test_im.test_im_handler import TestImHandler


class UsersTestsBase(BaseTest):
    aggregator: Aggregator = None
    collector: Collector = None
    testim_handler: TestImHandler = TestImHandler()
    test_im_params = {}

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.ui_client.users.create_4_local_users_all_combinations(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass

