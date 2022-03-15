import functools
import allure
from infra.common_utils import wait_for_predict_condition

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
    timeout = timeout or MAX_WAIT_FOR_STATUS
    predict_condition_func = functools.partial(management.is_collector_status_running_in_mgmt, collector)
    wait_for_predict_condition(predict_condition_func=predict_condition_func, timeout_sec=timeout,
                               interval_sec=COLLECTOR_KEEPALIVE_INTERVAL)
