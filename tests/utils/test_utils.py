import time
import allure
from infra.system_components.collectors.reporter_utils import attach_log_to_allure_report
from contextlib import contextmanager
from infra.allure_report_handler.reporter import Reporter


class TestUtils:

    @staticmethod
    @contextmanager
    def append_log_to_report_on_failure_context(collector, log_path):
        try:
            yield
        except Exception as e:
            Reporter.report(f"Operation/Validation failed {e}, attach the log to report: {log_path}")
            attach_log_to_allure_report(collector, log_path)
            raise e

    @staticmethod
    @allure.step("Wait max {timeout_sec} for the predict condition")
    def wait_for_predict_condition(predict_condition_func, timeout_sec, interval_sec):
        is_condition = predict_condition_func()
        start_time = time.time()
        while not is_condition and time.time() - start_time < timeout_sec:
            Reporter.report(f"Predict is still false, going to sleep {interval_sec}")
            time.sleep(interval_sec)
            is_condition = predict_condition_func()
        assert is_condition, f"Predict {predict_condition_func} still false after waiting {timeout_sec} seconds"
        Reporter.report(f"Got the expected condition: {predict_condition_func}")

