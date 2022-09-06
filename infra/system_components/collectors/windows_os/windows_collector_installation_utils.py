import allure
from infra.allure_report_handler.reporter import Reporter
import third_party_details

TARGET_BAT_FILES_PATH = "C:\\HelperBatFiles"
TARGET_VERSIONS_FOLDER_PATH = "C:\\Versions"


@allure.step("Create script that stop collector")
def create_stop_collector_script(collector_agent,
                                 registration_password: str):
    """
    Creating script for stopping the collector,
    we can stop it directly with the "collector.stop_collector" but it can cause remote connection issues against
    windows station because the status code is not 0 (means that command didn't finished succesfully) so we wrap the
    command with .bat file which return the output of the "FortiEdrService --stop -rp:{password}" and exit code 0 anyway
    :param collector_agent: collector agent
    :param registration_password: registration password we want to try stop collector with
    :return: script full path on OS
    """
    script_name = 'stop_collector.bat'
    script_content = _get_stop_collector_script_content(regsitration_password=registration_password)

    full_path = _create_bat_script_on_os(collector_agent=collector_agent,
                                         script_name=script_name,
                                         script_content=script_content)
    return full_path


@allure.step("Creating script for uninstalling the {collector_agent}")
def create_uninstallation_script(collector_agent, registration_password: str, logs_file_path: str):
    """ Creating script for uninstalling the collector """
    script_name = 'uninstall_collector.bat'
    script_content = _get_uninstallation_script_content(registration_password, logs_file_path)

    full_path = _create_bat_script_on_os(collector_agent=collector_agent,
                                         script_name=script_name,
                                         script_content=script_content)
    Reporter.report(f"Created uninstallation script in {full_path} with logs to "
                    f"{logs_file_path}")

    return full_path


def _create_bat_script_on_os(collector_agent,
                             script_name: str,
                             script_content: str):
    script_folder_path = collector_agent.os_station.create_new_folder(folder_path=fr'{TARGET_BAT_FILES_PATH}')
    script_full_path = fr'{script_folder_path}\{script_name}'

    if collector_agent.os_station.is_path_exist(path=script_full_path):
        collector_agent.os_station.remove_file(file_path=script_full_path)

    collector_agent.os_station.overwrite_file_content(content=script_content, file_path=script_full_path)
    return script_full_path


def _get_uninstallation_script_content(registration_password, logs_file_path):
    script_content = f"""for /f %%a in (
    'wmic product where "Name='Fortinet Endpoint Detection and Response Platform'" get IdentifyingNumber^^^|findstr "{{"'
    ) do set "val=%%a"
    msiexec.exe /x %val% /qn UPWD="{registration_password}" RMCONFIG=1 /l*vx {logs_file_path}
    """

    return script_content


def _get_stop_collector_script_content(regsitration_password):
    script_content = fr"""cd C:\Program Files\Fortinet\FortiEDR\
FortiEDRCollectorService.exe --stop -rp:{regsitration_password}
exit /b 0"""
    return script_content


@allure.step("Creating installer with version {version}")
def get_installer_path(collector, version):
    """ Getting the desired installer file from the shared folder """
    installer_file_name = _generate_installer_file_name(collector, version)
    files_path_in_local_machine = rf'{TARGET_VERSIONS_FOLDER_PATH}\{version}'
    shared_drive_path = rf'{third_party_details.SHARED_DRIVE_VERSIONS_PATH}\{version}'

    installation_files_folder = collector.os_station.copy_files_from_shared_folder(
        target_path_in_local_machine=files_path_in_local_machine,
        shared_drive_path=shared_drive_path,
        shared_drive_user_name=third_party_details.USER_NAME,
        shared_drive_password=third_party_details.PASSWORD,
        files_to_copy=[installer_file_name])

    full_installation_file_path = fr'{installation_files_folder}\{installer_file_name}'
    assert collector.os_station.is_path_exist(path=full_installation_file_path), \
        f"Desired installer file: {installer_file_name} is not found in {installation_files_folder}"
    Reporter.report(f"Installer created in: {full_installation_file_path}")
    return full_installation_file_path


def _generate_installer_file_name(collector, version):
    installer_file_name = fr"FortiEDRCollectorInstaller#archi#_{version}.msi"
    os_architecture = collector.os_station.os_architecture
    if '64-bit' in os_architecture:
        installer_file_name = installer_file_name.replace('#archi#', '64')
    elif '32-bit' in os_architecture:
        installer_file_name = installer_file_name.replace('#archi#', '32')
    else:
        raise Exception(
            f"Can not conduct installer file name, os station architecture is unknown: {os_architecture}"
        )
    return installer_file_name


def generate_installation_cmd(installer_path, agg_ip, agg_port, registration_pass, logs_path, organization=None):
    if organization is None:
        organization = ''
    else:
        organization = f'ORG={organization}'
    cmd = rf'msiexec /i "{installer_path}" /qn AGG={agg_ip}:{agg_port} PWD={registration_pass} {organization} /LIME {logs_path}'
    Reporter.report(f"cmd for installation: {cmd}")
    return cmd
