import functools
from contextlib import contextmanager
import allure
import logging
from infra.common_utils import wait_for_predict_condition

logger = logging.getLogger(__name__)

MAX_WAIT_FOR_PID = 10
PID_INTERVAL = 1
COLLECTOR_KEEPALIVE_INTERVAL = 5
MAX_WAIT_FOR_STATUS = 5 * 60


@allure.step("Wait until pid of {collector} appears")
def wait_until_collector_pid_appears(collector, timeout=None):
    _wait_for_process_id(collector=collector, is_alive=True, timeout=timeout)


@allure.step("Wait until pid of {collector} disappears")
def wait_until_collector_pid_disappears(collector, timeout=None):
    _wait_for_process_id(collector=collector, is_alive=False, timeout=timeout)


def _wait_for_process_id(collector, is_alive, timeout=None):
    """ If collector is alive so pid should not be None """
    log_msg = "appear" if is_alive else "disappear"
    logger.info(f"Wait for collector pid to {log_msg}")
    timeout = timeout or MAX_WAIT_FOR_PID

    def is_expected_pid():
        current_pid = collector.get_current_process_id()
        if is_alive:
            is_correct_pid = current_pid is not None
        else:
            is_correct_pid = current_pid is None
        return is_correct_pid

    wait_for_predict_condition(predict_condition_func=is_expected_pid,
                               timeout_sec=timeout, interval_sec=PID_INTERVAL)


@allure.step("Wait until status of {collector} in {management} is running")
def wait_for_running_collector_status_in_mgmt(management, collector, timeout=None):
    logger.info(f"Wait until status of {collector} in {management} is running")
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = functools.partial(management.is_collector_status_running_in_mgmt, collector)
    wait_for_predict_condition(predict_condition_func=predict_condition_func, timeout_sec=timeout,
                               interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)


@allure.step("Wait until status of {collector} in {management} is 'Disconnected'")
def wait_for_disconnected_collector_status_in_mgmt(management, collector, timeout=None):
    logger.info(f"Wait until status of {collector} in {management} is 'Disconnected'")
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = functools.partial(management.is_collector_status_disconnected_in_mgmt, collector)
    wait_for_predict_condition(predict_condition_func=predict_condition_func,
                               timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)


@allure.step("Wait until status of {collector} in {management} is 'Disabled'")
def wait_for_disabled_collector_status_in_mgmt(management, collector, timeout=None):
    logger.info(f"Wait until status of {collector} in {management} is 'Disabled'")
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = functools.partial(management.is_collector_status_disabled_in_mgmt, collector)
    wait_for_predict_condition(predict_condition_func=predict_condition_func,
                               timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)


@allure.step("Wait for a running status of {collector} in cli")
def wait_for_running_collector_status_in_cli(collector, timeout=None):
    logger.info(f"Wait for a running status of {collector} in cli")
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = collector.is_status_running_in_cli
    wait_for_predict_condition(predict_condition_func=predict_condition_func,
                               timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)


@allure.step("Wait for a disabled status of {collector} in cli")
def wait_for_disabled_collector_status_in_cli(collector, timeout=None):
    logger.info(f"Wait for a disabled status of {collector} in cli")
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = collector.is_status_disabled_in_cli
    wait_for_predict_condition(predict_condition_func=predict_condition_func,
                               timeout_sec=timeout, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)


@contextmanager
def collector_safe_operations_context(collector, is_running=True):
    condition = collector.is_status_running_in_cli if is_running else collector.is_status_down_in_cli
    assert condition(), f"{collector} status is not correct before performing the actions"
    check_if_collectors_has_crashed([collector])

    try:
        yield
    finally:
        assert condition(), f"{collector} status is not correct after performing the actions"
        check_if_collectors_has_crashed([collector])


@allure.step("Check if collectors has crashed")
def check_if_collectors_has_crashed(collectors_list):
    logger.debug("Check if collectors has crashed")
    crashed_collectors = []
    if collectors_list is not None and len(collectors_list) > 0:
        for collector in collectors_list:
            if collector.has_crash():
                crashed_collectors.append(f'{collector}')

        if len(crashed_collectors) > 0:
            assert False, f"Crash was detected in the collectors: {str(crashed_collectors)}"

    else:
        assert False, "Didn't pass any collector"
