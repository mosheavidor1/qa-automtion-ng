from infra.enums import LinuxDistroTypes

DISTRO_DETAILS_BY_TYPE = {  # define distro formatted details for later use in linux collectors
    LinuxDistroTypes.UBUNTU: {
        "version_name": 'Ubuntu20.04',
        "package_name_suffix": "deb",
        "commands": {
            "installed_packages": "dpkg --list",  # Don't use 'apt list --installed' is not stable
            "purge_package": "dpkg --purge",
            "install_package": "apt install -y"
        }
    },
    LinuxDistroTypes.CENTOS: {
        "version_name": 'CentOS7',
        "package_name_suffix": "x86_64.rpm",
        "commands": {
            "installed_packages": "rpm -qa",
            "purge_package": "rpm -e",
            "install_package": "yum install -y"
        }
    }
}


class LinuxDistroDetails:
    def __init__(self, distro_type):
        self._all_data = DISTRO_DETAILS_BY_TYPE[distro_type]
        self.distro_type = distro_type
        self.commands = LinuxDistroCommands(distro_type)
        self.version_name = self._all_data["version_name"]
        self.packages_suffix = self._all_data["package_name_suffix"]


class LinuxDistroCommands:
    def __init__(self, distro_type):
        self._all_commands = DISTRO_DETAILS_BY_TYPE[distro_type]["commands"]
        self.install = self._all_commands["install_package"]
        self.uninstall = self._all_commands["purge_package"]
        self.installed_packages = self._all_commands["installed_packages"]
