import allure
from infra.enums import SystemState


class CollectorUtils:

    @staticmethod
    @allure.step("{0} - Validate collector stopped")
    def validate_collector_stopped(collector):
        """ Validate that collector stopped:
        1. Collector should return correct status (not running).
        2. PID should be None.
        """
        pid = collector.get_current_process_id()
        assert collector.get_collector_status() == SystemState.NOT_RUNNING, \
            f"Collector on host {collector} was not stopped, pid is {pid}"
        assert pid is None, \
            f"Collector on host {collector} returning wrong status because pid {pid} still exists"

    @staticmethod
    @allure.step("{0} - Validate collector is currently running")
    def validate_collector_is_currently_running(collector):
        collector_status = collector.get_collector_status()
        assert collector_status == SystemState.RUNNING, f"{collector} is not running"
