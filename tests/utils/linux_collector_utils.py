import allure
from infra.enums import LinuxDistroTypes


class LinuxCollectorUtils:

    @staticmethod
    @allure.step("Validate linux collector uninstallation cmd output")
    def validate_uninstallation_cmd_output(cmd_output, linux_collector):
        if linux_collector.distro_type == LinuxDistroTypes.CENTOS:
            _validate_uninstallation_cmd_output_centos(cmd_output)
        elif linux_collector.distro_type == LinuxDistroTypes.UBUNTU:
            _validate_uninstallation_cmd_output_ubuntu(cmd_output)
        else:
            raise Exception(f"{linux_collector.distro_type} is not supported yet for this validation")


def _validate_uninstallation_cmd_output_centos(cmd_output):
    actual_removed_symlinks = cmd_output.split('\n')
    expected_removed_symlinks = ['Removed symlink /etc/systemd/system/multi-user.target.wants/fortiedr.service.',
                                 'Removed symlink /etc/systemd/system/fortiedr.service.']
    assert len(actual_removed_symlinks) == len(expected_removed_symlinks)
    for expected_symlink in expected_removed_symlinks:
        assert expected_symlink in actual_removed_symlinks, \
            f"Uninstallation cmd output does not contain {expected_symlink}"


def _validate_uninstallation_cmd_output_ubuntu(cmd_output):
    assert "Purging configuration files for fortiedrcollectorinstaller" in cmd_output, "Wrong msg after uninstallation"
