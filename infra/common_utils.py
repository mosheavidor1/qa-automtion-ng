import os
import shlex
import sys

import allure
import time
import logging

import third_party_details
from infra.allure_report_handler.reporter import Reporter

WAIT_FOR_COLLECTOR_NEW_CONFIGURATION = 60  # time to wait for collector new configuration

logger = logging.getLogger(__name__)


@allure.step("Wait max {timeout_sec} seconds for the condition: '{condition_msg}'")
def wait_for_condition(condition_func, timeout_sec, interval_sec, condition_msg):
    logger.info(f"Wait max {timeout_sec} sec for this condition: {condition_msg}")
    is_condition_met = condition_func()
    start_time = time.time()
    while not is_condition_met and time.time() - start_time < timeout_sec:
        logger.info(f"Sleep {interval_sec} sec because condition is still not met")
        time.sleep(interval_sec)
        logger.info("Check again if condition is met")
        is_condition_met = condition_func()
    assert is_condition_met, f"Timeout: after waiting max {timeout_sec} seconds, " \
                             f"this condition was NOT met !!!: \n '{condition_msg}'"
    logger.info(f"This condition was met: '{condition_msg}'")


@allure.step("Copy {file_name} from versions folder in shared folder to the slave that running the test")
def copy_file_from_shared_versions_folder_to_linux_jenkins_slave(file_name: str):
    if hasattr(sys, 'getwindowsversion'):
        raise Exception("Can not use this method on Windows machine")

    # create new folder on slave
    current_folder = os.path.dirname(os.path.realpath(__file__))
    new_folder_path = os.path.join(current_folder, "tmp")
    os.system(f'mkdir -p {new_folder_path}')

    new_file_path = os.path.join(new_folder_path, file_name).replace("\\", "/").replace("//", "/")
    splitted = new_file_path.split('/')
    filtered = splitted[:splitted.index('tmp') + 1] + [splitted[-1]]
    new_file_path = '/'.join(filtered)
    logger.info(f"new file path: {new_file_path}")

    # copy the file to the new created folder
    cmd = f"wget -O {new_file_path} http://{third_party_details.AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{third_party_details.LATEST_VERSIONS_SERVICE_PORT}/get_file?file={shlex.quote(file_name)}"

    Reporter.report(rf"Going to run the command: {cmd} on the machine that running the tests", logger_func=logger.info)

    # check command output
    output = os.system(cmd)
    Reporter.report(f"command output: {output}", logger_func=logger.info)

    message = None
    if int(output) == 0:
        Reporter.report(f"Download succeeded, file path is: {new_file_path}", logger_func=logger.info)
        message = "File was found and downloaded"
    else:
        new_file_path = None
        Reporter.report(f"Failed to download {file_name}, ", logger_func=logger.info)
        message = f"Failed to download, error: {output}"

    return new_file_path, message
