import logging
from contextlib import contextmanager
import allure
from infra.enums import FortiEdrSystemState
from infra.system_components.aggregator import Aggregator

logger = logging.getLogger(__name__)


@contextmanager
def revive_aggregator_on_failure_context(aggregator: Aggregator):
    try:
        yield
    finally:
        with allure.step("Cleanup - start aggregator service if the system is not running"):
            if not aggregator.is_system_in_desired_state(desired_state=FortiEdrSystemState.RUNNING):
                logger.info(f"start aggregator {aggregator} service if the system is not running")
                aggregator.start_service()
