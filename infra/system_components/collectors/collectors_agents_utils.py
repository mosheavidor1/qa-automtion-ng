from contextlib import contextmanager
import allure
import logging
from infra.common_utils import wait_for_condition
from infra.system_components.collector import CollectorAgent
from .default_values import MAX_WAIT_FOR_PID, PID_INTERVAL

logger = logging.getLogger(__name__)


@allure.step("Wait until pid of {collector} appears")
def wait_until_collector_pid_appears(collector: CollectorAgent, timeout=None, interval=None):
    _wait_for_process_id(collector=collector, is_alive=True, timeout=timeout, interval=interval)


@allure.step("Wait until pid of {collector} disappears")
def wait_until_collector_pid_disappears(collector: CollectorAgent, timeout=None, interval=None):
    _wait_for_process_id(collector=collector, is_alive=False, timeout=timeout, interval=interval)


def _wait_for_process_id(collector: CollectorAgent, is_alive, timeout=None, interval=None):
    """ If collector is alive so pid should not be None """
    log_msg = "appear" if is_alive else "disappear"
    logger.info(f"Wait for collector pid to {log_msg}")
    timeout = timeout or MAX_WAIT_FOR_PID
    interval = interval or PID_INTERVAL

    def is_expected_pid():
        current_pid = collector.get_current_process_id()
        if is_alive:
            is_correct_pid = current_pid is not None
        else:
            is_correct_pid = current_pid is None
        return is_correct_pid

    wait_for_condition(condition_func=is_expected_pid, timeout_sec=timeout, interval_sec=interval,
                       condition_msg=f"Wait for collector pid to {log_msg}")


@contextmanager
def collector_safe_operations_context(collector: CollectorAgent, is_running=True):
    condition = collector.is_agent_running if is_running else collector.is_agent_down
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
