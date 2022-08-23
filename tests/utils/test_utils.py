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
