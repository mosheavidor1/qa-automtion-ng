import allure
import pytest
from tests.utils.collector_utils import CollectorUtils


@allure.epic("Collectors")
@allure.feature("Basic Functionality")
@pytest.mark.sanity
@pytest.mark.xray('EN-73287')
# def test_stop_start_collector_a(collector):
def test_stop_start_collector_a(management, collector):
    """
    1. Stop a running collector and validate it stopped.
    2. Start collector and validate it started successfully.
    """
    with allure.step(f"Stop {collector} and validate"):
        collector.stop_collector()
        CollectorUtils.validate_collector_stopped(collector)

    with allure.step(f"Start {collector} and validate"):
        collector.start_collector()
        CollectorUtils.validate_collector_is_currently_running_according_to_management(management=management,
                                                                                       collector=collector)
        # CollectorUtils.validate_collector_is_currently_running(collector)
