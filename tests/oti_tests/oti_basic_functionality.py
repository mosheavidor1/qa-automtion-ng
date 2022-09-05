import os
import time
import allure
import pytest
import logging

from infra.allure_report_handler.reporter import TEST_STEP, Reporter
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.os_x_collector import OsXCollector
from tests.utils.collector_utils import downgrade_collector_context
from tests.utils.collector_group_utils import new_group_with_collector_context
from tests.utils.oti_utils import build_content_according_to_specific_collector

logger = logging.getLogger(__name__)


@allure.epic("Collectors")
@allure.feature("OTI")
@pytest.mark.xray('EN-77483')
@pytest.mark.sanity
@pytest.mark.collector_sanity
@pytest.mark.oti
def test_basic_oti(management, aggregator, collector, jenkins_handler):
    """
    1. Upload the content build to management
    2. Update collector installer
    3. Check that collector was upgraded to the version of the content we uploaded

    Then the context manager new_group_with_collector_context will return collector back to his initial group and delete
    new group created for this test
    There is an open issue: test ends with crash EN-78290
    """
    collector_agent = collector
    build = build_content_according_to_specific_collector(management, collector_agent, jenkins_handler)
    initial_collector_version = collector_agent.initial_version
    collector_downgrade_version = os.getenv("oti_base_version", default='5.1.0.590')

    windows_version = None
    linux_version = None
    osx_version = None

    if isinstance(collector_agent, WindowsCollector):
        windows_version = initial_collector_version
    elif isinstance(collector_agent, LinuxCollector):
        linux_version = initial_collector_version
    elif isinstance(collector_agent, OsXCollector):
        raise Exception("OSX is not supported yet")

    with downgrade_collector_context(management, aggregator, collector_agent, collector_downgrade_version):
        with new_group_with_collector_context(management=management,
                                              collector_agent=collector_agent) as group_name:

            target_group_name = group_name[0]

            with TEST_STEP("Upload content to management"):
                management.upload_content(desired_content_num=int(build.buildno))

            with TEST_STEP(f"Set collector installer to the group {target_group_name}"):
                management.update_collector_installer(collector_groups=target_group_name,
                                                      organization=management.tenant.organization.get_name(),
                                                      windows_version=windows_version,
                                                      osx_version=osx_version,
                                                      linux_version=linux_version)

            with TEST_STEP(
                    f"Check that collector was upgraded via OTI to the initial collector version: {initial_collector_version}"):
                timeout = 120
                interval = 10
                is_upgraded = False
                start_time = time.time()
                while time.time() - start_time < timeout and not is_upgraded:
                    if collector_agent.get_version() == initial_collector_version:
                        is_upgraded = True
                    else:
                        Reporter.report(f"still does not updated with the desired version {initial_collector_version}, going to sleep {interval} seconds and check again")
                        time.sleep(interval)

                assert is_upgraded, f"Failed to upgrade the collector via OTI to version: {initial_collector_version} within {timeout} seconds "

            Reporter.report(
                f"Collector was upgraded successfully via OTI and now the version is: {collector_agent.get_version()}",
                logger_func=logger.info)