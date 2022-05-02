import json
import os

import allure
import pytest

from infra.allure_report_handler.reporter import Reporter, TEST_STEP


@pytest.mark.create_environment
def test_validate_env_ready_for_run(setup_environment):

    system_components = setup_environment.get('system_components')
    collectors = setup_environment.get('collectors')

    with TEST_STEP("Write new setup details to myenv.txt file"):
        path = os.path.abspath('myenv.txt')
        with open(path, 'a') as env_file:
            env_file.write(f"SSH_ADMIN_USER={system_components.admin_user}\n")
            env_file.write(f"SSH_ADMIN_PASSWORD={system_components.admin_password}\n")
            env_file.write(f"ENVIRONMENT_ID={system_components.env_id}\n")
            env_file.write(f"DEFAULT_REGISTRATION_PASSWORD={system_components.registration_password}\n")
            env_file.write(f"ADMIN_REST_API_USER={system_components.admin_user}\n")
            env_file.write(f"ADMIN_REST_API_PASSWORD={system_components.admin_password}\n")
            env_file.write(f"MANAGEMENT_HOST_IP={system_components.management_ip}\n")

    with allure.step("Environment details"):
        Reporter.attach_str_as_file(file_name="System components", file_content=json.dumps(system_components.get_as_dict(), indent=4))
        Reporter.attach_str_as_file(file_name="Collectors", file_content=json.dumps(collectors, indent=4))

    is_failure_detected = False
    for key in collectors.keys():
        if 'failure' in key:
            is_failure_detected = True
            break

    assert not is_failure_detected, "Failed to deploy at least 1 collector"


