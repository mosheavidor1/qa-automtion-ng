import allure
import pytest

from tests.collector_tests.collectors_functionality_base import CollectorsTestsBase, \
    CollectorFunctionalityTestType


@allure.feature("Collectors")
@pytest.mark.sanity
class CollectorTests(CollectorsTestsBase):

    @pytest.mark.xray('EN-73287')
    def test_stop_start_collector(self, management):
        """
        1. Validate collector is running.
        2. Stop the collector and validate it stopped.
        3. Start collector and validate it started successfully.
        """
        self.management = management
        self.test_type = CollectorFunctionalityTestType.STOP_START_COLLECTOR
        self.play_test()
