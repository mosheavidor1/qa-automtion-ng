import time

from infra.allure_report_handler.reporter import Reporter


def short_retry(func):
    def inner(*args, **kwargs):
        num_retries = 3
        sleep_delay_sec = 5
        curr_try = 0
        while curr_try < num_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                curr_try += 1
                if curr_try == num_retries:
                    raise e
                time.sleep(sleep_delay_sec)
                Reporter.report(f"#{curr_try + 1} Try to invoke function with the name {func.__name__} failed, sleep {sleep_delay_sec} seconds ang trying again")
    return inner


def retry(func):
    def inner(*args, **kwargs):
        num_retries = 6
        sleep_delay_sec = 10
        curr_try = 0
        while curr_try < num_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                curr_try += 1
                if curr_try == num_retries:
                    raise e
                time.sleep(sleep_delay_sec)
                Reporter.report(f"#{curr_try + 1} Try to invoke function with the name {func.__name__} failed, sleep {sleep_delay_sec} seconds ang trying again")
    return inner
