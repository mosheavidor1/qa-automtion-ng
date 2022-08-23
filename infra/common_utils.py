import allure
import time
import logging

WAIT_FOR_COLLECTOR_NEW_CONFIGURATION = 60  # time to wait for collector new configuration

logger = logging.getLogger(__name__)


@allure.step("Wait max {timeout_sec} seconds for the condition: '{condition_msg}'")
def wait_for_condition(condition_func, timeout_sec, interval_sec, condition_msg):
    logger.info(f"Wait max {timeout_sec} sec for this condition: {condition_msg}")
    is_condition_met = condition_func()
    start_time = time.time()
    while not is_condition_met and time.time() - start_time < timeout_sec:
        logger.info(f"Sleep {interval_sec} sec because condition is still not met")
        time.sleep(interval_sec)
        logger.info("Check again if condition is met")
        is_condition_met = condition_func()
    assert is_condition_met, f"Timeout: after waiting max {timeout_sec} seconds, " \
                             f"this condition was NOT met !!!: \n '{condition_msg}'"
    logger.info(f"This condition was met: '{condition_msg}'")
