from contextlib import contextmanager
import allure
from infra.api.management_api.comm_control_policy import CommControlPolicy


@contextmanager
def change_comm_control_policy_mode_context(comm_control_policy: CommControlPolicy):
    old_mode = comm_control_policy.get_operation_mode()
    try:
        yield
    finally:
        with allure.step(f"Cleanup - return policy '{comm_control_policy}' to the original mode {old_mode}"):
            comm_control_policy.set_policy_mode(mode_name=old_mode, safe=True)

