import allure
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from tests.basic_test_lifecycle.base_test import BaseTest


class OrganizationTestsBase(BaseTest):
    test_im_params = {}

    aggregator: Aggregator = None
    collector: Collector = None

    @allure.step("Test prerequisites")
    def prerequisites(self):
        pass

    @allure.step("Run and validate")
    def run_and_validate(self):
        self.management.ui_client.organizations.create_organization(data=self.test_im_params)

    @allure.step("Reorder environment")
    def cleanup(self):
        pass
