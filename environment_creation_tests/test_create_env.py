import json

import allure
import pytest

from infra.allure_report_handler.reporter import Reporter


@pytest.mark.create_environment
def test_validate_env_ready_for_run(setup_environment):
    with allure.step("Environment details"):
        Reporter.attach_str_as_file(file_name="Environment details", file_content=json.dumps(setup_environment, indent=4))