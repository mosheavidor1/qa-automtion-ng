from enum import Enum

import aenum as aenum


class SystemState(Enum):
    RUNNING = 'Running'  # Status name from management
    NOT_RUNNING = 'NOT_RUNNING'
    DISCONNECTED = 'Disconnected'  # Status name from management
    DOWN = 'DOWN'
    DISABLED = 'Disabled'  # Status name from management
    ENABLED = 'ENABLED'


class ComponentType(Enum):
    MANAGEMENT = 'manager'
    BOTH = 'both'
    AGGREGATOR = 'aggregator'
    CORE = 'core'


class OsTypeEnum(Enum):
    WINDOWS = 'WINDOWS'
    LINUX = 'LINUX'
    OS_X = 'OS_X'


class CollectorTypes(aenum.Enum):
    _settings_ = aenum.NoAlias
    WINDOWS_11_64 = 'Windows 11'
    WINDOWS_10_64 = 'Windows 10'
    WINDOWS_10_32 = 'Windows 10'
    WINDOWS_8_64 = 'Windows 8.1'
    WINDOWS_8_32 = 'Windows 8.1'
    WINDOWS_7_64 = 'Windows 7'
    WINDOWS_7_32 = 'Windows 7'
    WIN_SERVER_2016 = 'Windows Server 2016'
    WIN_SERVER_2019 = 'Windows Server 2019'
    LINUX_CENTOS_6 = 'CentOS Linux 6'
    LINUX_CENTOS_7 = 'CentOS Linux 7'
    LINUX_CENTOS_8 = 'CentOS Linux 8'
    LINUX_UBUNTU_20 = 'Ubuntu 20'


class AutomationVmTemplates(Enum):
    # A Confluence page with updated template names should be followed:
    # http://confluence.ensilo.local/display/QA/Templates+and+preinstalled+application
    WIN_11X64 = 'TEMPLATE_WIN_11_64'
    WIN10_X64H2 = 'TEMPLATE_WIN_10_64_20H2'
    WIN10_X64 = 'TEMPLATE_WIN_10_64_LATEST'
    WIN10_X32 = 'TEMPLATE_WIN_10_32'
    WIN81_X64 = 'TEMPLATE_WIN_81_64'
    WIN81_X32 = 'TEMPLATE_WIN_81_32'
    WIN7_X64 = 'TEMPLATE_WIN_7_64'
    WIN7_X86 = 'TEMPLATE_WIN_7_86'

    WIN_SERV_2012 = 'AUTO_TEMPLATE_WIN_SERV_2012'
    WIN_SERV_2016 = 'TEMPLATE_SRV_2016_64'
    WIN_SERV_2019 = 'TEMPLATE_SRV_2019_64'
    WIN_SERV_2020 = 'AUTO_TEMPLATE_WIN_SERV_2020'
    WIN_SERV_2022 = 'AUTO_TEMPLATE_WIN_SERV_2022'

    LINUX_CENTOS_6 = 'TEMPLATE_CENTOS_6'
    LINUX_CENTOS_7 = 'TEMPLATE_CENTOS_7'
    LINUX_CENTOS_8 = 'TEMPLATE_CENTOS_8'
    LINUX_UBUNTU_16 = 'TEMPLATE_UBUNTU_16'
    LINUX_UBUNTU_18 = 'TEMPLATE_UBUNTU_18'
    LINUX_UBUNTU_20 = 'TEMPLATE_UBUNTU_20'
    LINUX_AMAZON = 'TEMPLATE__VT41_AMAZON'
    LINUX_ORACLE_77 = 'TEMPLATE_VT41_ORACLE_7.7'
    LINUX_ORACLE_80 = 'TEMPLATE_VT41_ORACLE_8_0'
    LINUX_ORACLE_81 = 'TEMPLATE_VT41_ORACLE_8_1'
    LINUX_ORACLE_82 = 'TEMPLATE_VT41_ORACLE_8.2'
    LINUX_ORACLE_83 = 'TEMPLATE_VT41_ORACLE_8.3'
    LINUX_SUSE = 'TEMPLATE_VT41_SUSE'

    AUTOMATION_SERVICES_MACHINE_TEMPLATE = 'AUTOMATION_SERVICES_MACHINE_TEMPLATE'
    CENTOS7_SYSTEM_COMPONENT_TEMPLATE = 'TEMPLATE_CENTOS7_COMPONENT'


class HttpRequestMethodsEnum(Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    TRACE = 'TRACT'
    OPTIONS = 'OPTIONS'


class ManagementUserRoles(Enum):
    ROLE_REST_API = 'ROLE_REST_API'
    ROLE_USER = 'ROLE_USER'
    ROLE_ADMIN = 'ROLE_ADMIN'
    ROLE_HOSTER = 'ROLE_HOSTER'


class LinuxDistroTypes(Enum):
    UBUNTU = 'UBUNTU'
    CENTOS = 'CENTOS'
