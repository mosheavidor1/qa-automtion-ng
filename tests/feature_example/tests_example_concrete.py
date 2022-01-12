import pytest

from infra.allure_report_handler.reporter import Reporter
from tests.feature_example.example_feature_base import ExampleFeatureBase


class ConcreteExampleTests(ExampleFeatureBase):

    # @pytest.mark.xray('EN-36193')
    @pytest.mark.example
    def test_first(self, one_management_one_aggregator_one_core_one_collector):
        self.management = one_management_one_aggregator_one_core_one_collector

        collector = self.management.collectors[0]
        collector.copy_installation_files_to_local_machine(version='5.0.10.204')
        pid = collector.process_id
        Reporter.report(f"collector process ID before stop: {pid}")
        has_crash = collector.has_crash()
        # has_dumps = collector.has_dumps()
        # collector.stop_collector(password='12345678')
        # collector.start_collector()
        # pid = collector.get_collector_process_id()
        # Reporter.report(f"collector process ID after start: {pid}")

        # print("finished")


