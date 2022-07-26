import allure
import time
from infra.allure_report_handler.reporter import Reporter

WAIT_FOR_COLLECTOR_NEW_CONFIGURATION = 60  # time to wait for collector new configuration


@allure.step("Wait max {timeout_sec} for the condition '{condition_func}'")
def wait_for_condition(condition_func, timeout_sec, interval_sec, err_msg=None):
    error_message = f"Condition '{condition_func}' is still false" if err_msg is None else err_msg
    is_condition = condition_func()
    start_time = time.time()
    while not is_condition and time.time() - start_time < timeout_sec:
        Reporter.report(f"{error_message}, going to sleep {interval_sec}")
        time.sleep(interval_sec)
        is_condition = condition_func()
    assert is_condition, f"{error_message}, after waiting {timeout_sec} seconds"
    Reporter.report(f"Got the expected condition: '{condition_func}'")
