import json
import time
import logging

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.forti_edr_versions_service_handler.forti_edr_versions_service_handler import FortiEdrVersionsServiceHandler
from infra.jenkins_utils.jenkins_handler import JenkinsHandler
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.utils.utils import StringUtils

logger = logging.getLogger(__name__)


@allure.step("Build content with Jenkins job: Content_Build_Collector_only")
def build_content_according_to_specific_collector(management: Management,
                                                  collector: CollectorAgent,
                                                  jenkins_handler: JenkinsHandler):
    job_name = "Content_Build_Collector_only"
    management_version = management.get_version()

    build_content_job_params = get_build_content_params_as_dict_according_to_collector_current_version(
        management=management_version,
        collector=collector,
        collector_version=collector.initial_version)

    with allure.step("Check if build with those params already exist in order to avoid triggering another job"
                     "with same params"):
        build_number = jenkins_handler.get_build_number_according_to_params_if_exist(job_name=job_name,
                                                                                     job_params=build_content_job_params)

        if build_number is not None:
            return build_number

    with allure.step(f"Did not found job with the desired param, going to trigger {job_name}"):
        job_timeout = 5*60
        sleep_interval = 10

        build = jenkins_handler.start_job(job_name=job_name,
                                          job_params=build_content_job_params)
        build_number = build.buildno
        Reporter.report(f"Build number is :{build_number}", logger_func=logger.info)
        state = jenkins_handler.wait_for_build_concrete_state(build=build, timeout=job_timeout, sleep_interval=sleep_interval)
        if state != 'SUCCESS':
            assert False, f"Job Content_Build_Collector_only with build {build_number} Failed, Stopping test"

    wait_until_content_file_appear_in_shared_folder(build_number_of_content_job_in_jenkins=build_number)

    return build_number


@allure.step("Wait until content will appear in shared folder")
def wait_until_content_file_appear_in_shared_folder(build_number_of_content_job_in_jenkins: str,
                                                    timeout: int = 3*60,
                                                    interval: int = 5):
    Reporter.report("Wait until content file created in shared folder", logger_func=logger.info)
    start_time = time.time()

    is_found = False
    while time.time() - start_time < timeout and not is_found:
        result = FortiEdrVersionsServiceHandler.get_latest_content_files_from_shared_folder(
            num_last_content_files=5)
        expected_file_name = f"FortiEDRCollectorContent-{build_number_of_content_job_in_jenkins}.nslo"
        if expected_file_name in result:
            is_found = True
            Reporter.report(f"{expected_file_name} is found in shared folder", logger_func=logger.info)
        else:
            Reporter.report(f"{expected_file_name} does not appear in shared folder yet, going to sleep {interval} seconds", logger.info)
            time.sleep(interval)

    assert is_found, f"content file that should be created according to build {build_number_of_content_job_in_jenkins} is not created within {timeout} seconds"


def get_build_content_params_body_as_dict():
    return {
        'content_branch': 'master',
        'ensilomgmt_branch': '',
        'ENSILO_VERSION': '',
        'brandName': 'FortiEDR',
        'min_core_version': '',
        'min_management_version': '',
        'WINDOWS_COLLECTOR_VERSION': '',
        'OSX_COLLECTOR_VERSION': '',
        'CENTOS6_COLLECTOR_VERSION': '',
        'CENTOS7_COLLECTOR_VERSION': '',
        'CENTOS8_COLLECTOR_VERSION': '',
        'ORACLE6_COLLECTOR_VERSION': '',
        'ORACLE7_COLLECTOR_VERSION': '',
        'ORACLE8_COLLECTOR_VERSION': '',
        'Ubuntu1604_COLLECTOR_VERSION': '',
        'Ubuntu1804_COLLECTOR_VERSION': '',
        'Ubuntu2004_COLLECTOR_VERSION': '',
        'AmazonLinux_COLLECTOR_VERSION': '',
        'SLES15_COLLECTOR_VERSION': '',
        'SLES12_COLLECTOR_VERSION': ''
    }


def get_branch_name_from_mgt_version(base_version):
    branch_dict = {
        "4.1.0": "golf-p1",
        "4.5.1": "golf-p4",
        "5.0.2": "honda-p2-HF1",
        "5.0.3": "honda-p2-HF2",
        "5.1.0": "infinity-p1",
        "5.2.0": "infinity-p2",
        "5.2.1": "jaguar",
        "6.0.0": "jeep-p2"
    }
    return branch_dict[base_version]


@allure.step("Get params for job Content_Build_Collector_only according to collector type")
def get_build_content_params_as_dict_according_to_collector_current_version(management_version: str,
                                                                            collector: CollectorAgent,
                                                                            collector_version: str):
    params = get_build_content_params_body_as_dict()
    management_base_version = StringUtils.get_txt_by_regex(text=management_version, regex='(\d+.\d+.\d+).\d+',
                                                           group=1)

    if 'windows' in collector.os_station.os_name.lower():
        params['WINDOWS_COLLECTOR_VERSION'] = collector_version

    elif 'centos' in collector.os_station.os_name.lower():
        params['CENTOS6_COLLECTOR_VERSION'] = collector_version
        params['CENTOS7_COLLECTOR_VERSION'] = collector_version
        params['CENTOS8_COLLECTOR_VERSION'] = collector_version
    else:
        raise Exception(f"This test is not supported for {collector.os_station.os_name.lower()}")

    branch = get_branch_name_from_mgt_version(management_base_version)
    params['ensilomgmt_branch'] = 'release/' + branch
    params['ENSILO_VERSION'] = management_base_version

    Reporter.report(f"Job params are: {json.dumps(params, indent=4)}", logger_func=logger.info)

    return params
