import os
import time
import allure
import pytest
import logging
from packaging import version

from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from infra.system_components.aggregator import Aggregator
from infra.jenkins_utils.jenkins_handler import JenkinsHandler
from infra.allure_report_handler.reporter import TEST_STEP, Reporter
from infra.utils.utils import StringUtils
from tests.utils.collector_utils import downgrade_collector_context, revive_collector_agent_on_failure_context
from tests.utils.collector_group_utils import new_group_with_collector_context
from tests.utils.oti_utils import build_content_according_to_specific_collector, upload_invalid_oti_file, \
    set_installer_to_group

logger = logging.getLogger(__name__)


# @allure.epic("Collectors")
# @allure.epic("Management")
# @allure.feature("OTI")
# @pytest.mark.xray('EN-77483')
# @pytest.mark.e2e_windows_collector_full_regression
# @pytest.mark.e2e_linux_collector_full_regression
# @pytest.mark.e2e_windows_collector_sanity
# @pytest.mark.e2e_linux_collector_sanity
# @pytest.mark.oti
# @pytest.mark.oti_sanity
# def test_basic_oti(management: Management,
#                    aggregator: Aggregator,
#                    collector: CollectorAgent,
#                    jenkins_handler: JenkinsHandler):
#     # TODO - NEED TO ADD MECHANISM THAT UPLOAD THE FILE AND WAIT TILL VALIDATION ENDS
#     # IN ORDER TO AVOID RACE CONDITION IN PARALLEL TESTS - THEN, uncomment THE sanity marks
#     """
#     1. Upload the content build to management
#     2. Update collector installer
#     3. Check that collector was upgraded to the version of the content we uploaded
#
#     Then the context manager new_group_with_collector_context will return collector back to his initial group and delete
#     new group created for this test
#     """
#     collector_agent = collector
#     initial_collector_version = collector_agent.initial_version
#     build = build_content_according_to_specific_collector(management=management,
#                                                           collector=collector_agent,
#                                                           jenkins_handler=jenkins_handler,
#                                                           collector_specific_version=initial_collector_version)
#
#     collector_downgrade_version = os.getenv("oti_base_version", default='5.1.0.590')
#
#     with downgrade_collector_context(management, aggregator, collector_agent, collector_downgrade_version):
#         with new_group_with_collector_context(management=management,
#                                               collector_agent=collector_agent) as group_name:
#             target_group_name = group_name[0]
#
#             set_installer_to_group(management=management,
#                                    collector=collector,
#                                    build_number=int(build.buildno),
#                                    group_name=target_group_name)
#
#             with TEST_STEP(
#                     f"Check that collector was upgraded via OTI to the initial collector version: {initial_collector_version}"):
#                 timeout = 120
#                 interval = 10
#                 is_upgraded = False
#                 start_time = time.time()
#                 while time.time() - start_time < timeout and not is_upgraded:
#                     if collector_agent.get_version() == initial_collector_version:
#                         is_upgraded = True
#                     else:
#                         Reporter.report(
#                             f"still does not updated with the desired version {initial_collector_version}, going to sleep {interval} seconds and check again")
#                         time.sleep(interval)
#
#                 assert is_upgraded, f"Failed to upgrade the collector via OTI to version: {initial_collector_version} within {timeout} seconds "
#
#             Reporter.report(
#                 f"Collector was upgraded successfully via OTI and now the version is: {collector_agent.get_version()}",
#                 logger_func=logger.info)
#     collector_agent.update_process_id()


@allure.epic("Management")
@allure.feature("OTI")
@pytest.mark.xray('EN-78301')
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_linux_collector_sanity
@pytest.mark.oti
@pytest.mark.oti_sanity
def test_upload_oti_invalid_content(management: Management):
    """
    Upload a content with the right extension, but with invalid content.
    File should not be parsed by management and return an error.
    """
    with TEST_STEP("Check that uploading invalid content will not be accepted and will return an error"):
        file_name = StringUtils.generate_random_string(length=5)
        name = f"otiTest_{file_name}.nslo"
        upload_invalid_oti_file(management=management,
                                name=name)


@allure.epic("Management")
@allure.feature("OTI")
@pytest.mark.xray('EN-68446')
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_linux_collector_sanity
@pytest.mark.oti
@pytest.mark.oti_sanity
def test_oti_upload_incompatible_file(management: Management):
    """
    Upload a content with the wrong extension, only nslo extension should be uploaded by management
    File should not be uploaded by management and return an error.
    """
    with TEST_STEP("Check that uploading file with wrong extension- here .txt, will not be accepted and will return "
                   "an error"):
        file_name = StringUtils.generate_random_string(length=5)
        name = f"otiTest_{file_name}.txt"
        upload_invalid_oti_file(management=management,
                                name=name)


# @allure.epic("Management")
# @allure.feature("OTI")
# @pytest.mark.xray('EN-68979')
# @pytest.mark.e2e_windows_collector_full_regression
# @pytest.mark.e2e_linux_collector_full_regression
# @pytest.mark.e2e_windows_collector_sanity
# @pytest.mark.e2e_linux_collector_sanity
# @pytest.mark.oti
# @pytest.mark.oti_sanity
# def test_oti_upload_older_content(management: Management,
#                                   aggregator: Aggregator,
#                                   collector: CollectorAgent,
#                                   jenkins_handler: JenkinsHandler):
#     """
#     Upload a content with older version than current collector version to management.
#     Group should be updated with the older version but collector should not be updated with older version.
#     #TODO when we will add 2 collectors for testing:
#     Add a collector with a version lower than content version and check that it was updated with the content version
#     """
#     collector_agent = collector
#     collector_downgrade_version = os.getenv("oti_base_version", default='5.1.0.590')
#     initial_collector_version = collector_agent.get_version()
#
#     build = build_content_according_to_specific_collector(management=management,
#                                                           collector=collector_agent,
#                                                           jenkins_handler=jenkins_handler,
#                                                           collector_specific_version=collector_downgrade_version)
#
#     if version.parse(collector_downgrade_version) > version.parse(initial_collector_version):
#         assert False, "Cannot test with collector base version higher than actual version"
#
#     with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
#                                                    aggregator=aggregator, revived_version=initial_collector_version):
#
#         with new_group_with_collector_context(management=management,
#                                               collector_agent=collector_agent) as group_name:
#
#             target_group_name = group_name[0]
#
#             set_installer_to_group(management=management,
#                                    collector=collector,
#                                    build_number=int(build.buildno),
#                                    group_name=target_group_name)
#
#             with TEST_STEP(
#                     f"Check that collector was not downgraded via OTI to the base collector version: {collector_downgrade_version}"):
#                 timeout = 120
#                 interval = 10
#                 is_upgraded = False
#                 start_time = time.time()
#                 while time.time() - start_time < timeout and not is_upgraded:
#                     if collector_agent.get_version() != initial_collector_version:
#                         is_upgraded = True
#                     else:
#                         Reporter.report(
#                             f"Still not updated with the downgrade version {collector_downgrade_version} as expected, going to sleep {interval} seconds and check again")
#                         time.sleep(interval)
#
#                 assert is_upgraded is False, f"Collector should not be upgraded via OTI "
#
#             Reporter.report(
#                 f"OTI failed as expected, collector wasn't downgraded, the collector version is: {collector_agent.get_version()}",
#                 logger_func=logger.info)
#         collector_agent.update_process_id()