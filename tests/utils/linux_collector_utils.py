import re

import allure
from infra.enums import LinuxDistroTypes


class LinuxCollectorUtils:

    @staticmethod
    @allure.step("Validate linux collector uninstallation cmd output")
    def validate_uninstallation_cmd_output(cmd_output, linux_collector):
        if linux_collector.distro_type == LinuxDistroTypes.CENTOS:
            is_centos6 = linux_collector.os_station.distro_data.version_name.lower() == 'centos6'
            _validate_uninstallation_cmd_output_centos(cmd_output, is_centos6)
        elif linux_collector.distro_type == LinuxDistroTypes.UBUNTU:
            _validate_uninstallation_cmd_output_ubuntu(cmd_output)
        else:
            raise Exception(f"{linux_collector.distro_type} is not supported yet for this validation")


def _validate_uninstallation_cmd_output_centos(cmd_output: str, is_centos6=False):
    if is_centos6:
        assert cmd_output in ['', None], f"Uninstallation cmd out is not empty: {cmd_output}"
        return

    actual_removed_symlinks = cmd_output.splitlines()
    expected_removed_symlinks = [r'Removed (?:symlink )?/etc/systemd/system/multi-user.target.wants/fortiedr.service.',
                                 r'Removed (?:symlink )?/etc/systemd/system/fortiedr.service.']
    assert len(actual_removed_symlinks) == len(expected_removed_symlinks)
    for expected_symlink in expected_removed_symlinks:
        match = re.findall(expected_symlink, cmd_output)
        assert len(match) > 0, f"Uninstallation cmd output does not contain {expected_symlink}"


def _validate_uninstallation_cmd_output_ubuntu(cmd_output):
    assert "Purging configuration files for fortiedrcollectorinstaller" in cmd_output, "Wrong msg after uninstallation"
