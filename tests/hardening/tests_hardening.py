import os

from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import FORTI_EDR_DRIVERS_FOLDERS
import allure
import pytest
from infra.enums import FortiEdrSystemState
from infra.allure_report_handler.reporter import Reporter, TEST_STEP
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.management import Management
from infra.system_components.aggregator import Aggregator
from infra.utils.utils import StringUtils
from tests.hardening.hardening_utils import ManipulateEdrDriversEnum
from tests.utils.collector_utils import revive_collector_agent_on_failure_context, downgrade_collector_context
import logging

logger = logging.getLogger(__name__)


@allure.epic("Collector")
@allure.feature("Hardening")
@pytest.mark.xray('EN-72806')
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.e2e_linux_collector_sanity
@pytest.mark.e2e_linux_collector_sanity_parallel
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.hardening_windows_sanity
@pytest.mark.hardening_linux_sanity
@pytest.mark.hardening_windows
@pytest.mark.hardening_linux
def test_upgrade_collector(management: Management,
                           aggregator: Aggregator,
                           collector: CollectorAgent):
    """
    1- Get version to downgrade
    2- Uninstall collector
    3- Install version_to_downgrade version
    4- Upgrade to the version the collector started the test with
    5- Check upgrade collector successfully
    """
    collector_agent = collector
    desired_collector_version = collector_agent.get_version()
    registration_password = management.tenant.organization.registration_password
    with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
                                                   aggregator=aggregator, revived_version=desired_collector_version):
        version_to_downgrade = os.getenv("oti_base_version", default='5.1.0.590')
        with downgrade_collector_context(management=management, aggregator=aggregator, collector_agent=collector_agent,
                                         version_to_downgrade=version_to_downgrade):
            Reporter.report(
                f"Downgrading collector to version: {version_to_downgrade}")
            collector_agent.upgrade_collector(desired_version=desired_collector_version,
                                              registration_password=registration_password)
            if collector_agent.get_version() != desired_collector_version:
                assert False, f"Collector failed to upgrade to version : {desired_collector_version}, actual version is: {collector_agent.get_version()}"
            else:
                Reporter.report(
                    f"Upgrade collector successfully to version: {collector_agent.get_version()}")


@allure.epic("Collector")
@allure.feature("Hardening")
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.hardening_windows_sanity
@pytest.mark.hardening_windows
@pytest.mark.parametrize(
    "xray, driver_name, manipulation_type",
    [('EN-81028', "FortiEDRAvDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81029', "FortiEDRBaseDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81019', "FortiEDRElamDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81020', "FortiEDRFsDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81023', "FortiEDRIotDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81024', "FortiEDRWinDriver", ManipulateEdrDriversEnum.DELETE),
     ('EN-81025', "FortiEDRNetFilter", ManipulateEdrDriversEnum.DELETE),

     ('EN-72829', "FortiEDRAvDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81017', "FortiEDRBaseDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81018', "FortiEDRElamDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81021', "FortiEDRFsDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81022', "FortiEDRIotDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81027', "FortiEDRWinDriver", ManipulateEdrDriversEnum.EDIT),
     ('EN-81026', "FortiEDRNetFilter", ManipulateEdrDriversEnum.EDIT)
     ],
)
def test_manipulate_drivers_in_system32(management: Management,
                                        aggregator: Aggregator,
                                        collector: CollectorAgent,
                                        xray: str,
                                        driver_name: str,
                                        manipulation_type: ManipulateEdrDriversEnum):
    f"""
    This test is only for windows collectors
    1- Check if the driver {driver_name} exists in the drivers folder: "C:\\Windows\\System32\\drivers"
    2- If it exists, try to delete it
    3- If succeeds, the test failed, because user should get PERMISSION DENIED when trying to delete a fortinet driver
    4- If failed the test passed successfully
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on Windows collector"
    collector_agent = collector
    collector_version = collector_agent.get_version()

    file_name = f"{driver_name}_{collector_version}.sys"
    full_driver_path = fr'{FORTI_EDR_DRIVERS_FOLDERS}\{file_name}'

    with TEST_STEP(f"Check if {full_driver_path} exists in the collector"):
        files = collector.os_station.get_list_of_files_in_folder(folder_path=FORTI_EDR_DRIVERS_FOLDERS,
                                                                 file_suffix='.sys')
        if full_driver_path not in files:
            assert False, f"The file {full_driver_path} was not found in the collector, can not test anything, check your system"

    with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
                                                   aggregator=aggregator, revived_version=collector_version):
        Reporter.report(
            f"Will try to {manipulation_type.value} the driver: {driver_name} and expect to be permission denied",
            logger_func=logger.info)

        with TEST_STEP(f"Try to {manipulation_type.value} {full_driver_path}"):

            if manipulation_type == ManipulateEdrDriversEnum.DELETE:
                output = collector_agent.os_station.remove_file(file_path=full_driver_path, force=True, safe=True)
                assert 'access is denied' in output.lower(), f"Did not found access is denied in output: {output}"

            elif manipulation_type == ManipulateEdrDriversEnum.EDIT:
                content = StringUtils.generate_random_string(length=5)
                output = collector_agent.os_station.overwrite_file_content(content=content, file_path=full_driver_path, safe=True)
                is_access_denied = "access is denied" in output.lower()
                is_process_cannot_access = "process cannot access the file because it is being used by another process." in output.lower()
                assert is_access_denied or is_process_cannot_access, 'Did not received "access denied message" or ' \
                                                                     '"process cannot access the file" when trying to ' \
                                                                     'edit the file, check if the process was ' \
                                                                     'edited - failing the test'
            else:
                raise NotImplemented(f"There is no logic for test with {manipulation_type.name}")

        Reporter.report(f"Access Denied when tried to {manipulation_type.value} as expected", logger_func=logger.info)

        if manipulation_type == ManipulateEdrDriversEnum.DELETE:
            with TEST_STEP(f"Checking if {full_driver_path} exists after trying to remove it"):
                files = collector.os_station.get_list_of_files_in_folder(folder_path=FORTI_EDR_DRIVERS_FOLDERS,
                                                                         file_suffix='.sys')
                if full_driver_path not in files:
                    assert False, f"Removing Fortinet driver {driver_name} should not be allowed and we removed it sucessfully, bug!"
                Reporter.report(f"The file: {file_name} exist, that means we failed to remove it as expected",
                                logger_func=logger.info)

            Reporter.report(f"The file: {file_name} exist, that means we failed to remove it as expected",
                            logger_func=logger.info)


@allure.epic("Collector")
@allure.feature("Hardening")
@pytest.mark.xray('EN-72805')
@pytest.mark.e2e_windows_collector_sanity
@pytest.mark.e2e_windows_collector_sanity_parallel
@pytest.mark.e2e_windows_collector_full_regression
@pytest.mark.hardening_windows_sanity
@pytest.mark.hardening_windows
def test_uninstall_windows_collector_wrong_password(management: Management,
                                                    aggregator: Aggregator,
                                                    collector: CollectorAgent):
    """
    1- Generate a random password
    2- Uninstall Windows collector with the created password
    3- Check that windows collector was not uninstalled and is still running without crashes
    """
    assert isinstance(collector, WindowsCollector), "This test should run only on windows collector"
    collector_agent = collector
    collector_version = collector_agent.get_version()
    start_time = collector_agent.get_current_datetime()
    registration_wrong_password = StringUtils.generate_random_string(length=5)
    Reporter.report(
        "Going to uninstall collector with a wrong password")
    with revive_collector_agent_on_failure_context(tenant=management.tenant,
                                                   collector_agent=collector_agent,
                                                   aggregator=aggregator,
                                                   revived_version=collector_version):
        collector_agent.uninstall_collector(registration_password=registration_wrong_password,
                                            expect_to_succeed=False)
        if collector_agent.get_version() != collector_version:
            assert False, f"Collector version has changed, it started with version {collector_version}," \
                          f" and is now version {collector_agent.get_version()}"
        assert collector_agent.is_string_in_logs(string_to_find=
                                                 'Incorrect Password',
                                                 first_log_date_time=start_time), "Incorrect password was not " \
                                                                                  "returned when uninstalling "

        status = collector_agent.get_agent_status()
        running = FortiEdrSystemState.RUNNING
        if collector_agent.has_crash():
            assert False, "Collector has crash, reviving collector!!"

        if status != running:
            assert False, "Collector is not running, reviving collector!!"

    Reporter.report("Uninstall failed as expected, collector is up and running")


@allure.epic("Collector")
@allure.feature("Hardening")
@pytest.mark.xray('EN-72824')
@pytest.mark.e2e_linux_collector_sanity
@pytest.mark.e2e_linux_collector_sanity_parallel
@pytest.mark.e2e_linux_collector_full_regression
@pytest.mark.hardening_linux
@pytest.mark.hardening_linux_sanity
@pytest.mark.parametrize(
    "xray, process_name",
    [('EN-81002', "FortiEDRCollector"),
     ('EN-72824', "FortiEDRAvScanner")],
)
def test_linux_kill_protected_process(management: Management,
                                      aggregator: Aggregator,
                                      collector: CollectorAgent,
                                      xray: str,
                                      process_name: str):
    """
    Try to kill FortiEDRCollector and FortiEDRAvScanner processes.
    Both should be protected and operation should not be permitted.
    If action was allowed, start collector again.

    1- Kill FortiEDRCollector and FortiEDRAvScanner processes
    2- Check that action was not permitted and collector is up and running
    3- Otherwise start it

    FortiEDRAvScanner can be killed, open issue: http://jira.ensilo.local/browse/EN-79168
    """
    assert isinstance(collector, LinuxCollector), "This test should run only on linux collector"
    collector_agent = collector
    collector_version = collector_agent.get_version()
    with revive_collector_agent_on_failure_context(tenant=management.tenant, collector_agent=collector_agent,
                                                   aggregator=aggregator, revived_version=collector_version):
        Reporter.report(
            f"Trying to kill protected {process_name} process", logger_func=logger.info)
        collector_agent.try_kill_fortiedr_process(process_name=process_name)

        status = collector_agent.get_agent_status()

        if status != FortiEdrSystemState.RUNNING:
            assert False, f"Collector should not be disabled, state is {status}"
        Reporter.report(
            f"Protected FortiEDR processes were not killed as expected", logger_func=logger.info)
