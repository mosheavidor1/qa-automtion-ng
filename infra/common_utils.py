import allure
import time
from infra.allure_report_handler.reporter import Reporter


@allure.step("Wait max {timeout_sec} for the condition '{condition_func}'")
def wait_for_condition(condition_func, timeout_sec, interval_sec):
    is_condition = condition_func()
    start_time = time.time()
    while not is_condition and time.time() - start_time < timeout_sec:
        Reporter.report(f"Condition '{condition_func}' is still false, going to sleep {interval_sec}")
        time.sleep(interval_sec)
        is_condition = condition_func()
    assert is_condition, f"Condition '{condition_func}' still false after waiting {timeout_sec} seconds"
    Reporter.report(f"Got the expected condition: '{condition_func}'")
