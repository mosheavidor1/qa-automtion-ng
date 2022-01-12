from enum import Enum


class SystemState(Enum):
    RUNNING = 'RUNNING'
    NOT_RUNNING = 'NOT_RUNNING'


class ComponentType(Enum):
    MANAGEMENT = 'manager'
    AGGREGATOR = 'aggregator'
    CORE = 'core'


class OsTypeEnum(Enum):
    WINDOWS = 'WINDOWS'
    LINUX = 'LINUX'
    OS_X = 'OS_X'


class CollectorTypes(Enum):
    WINDOWS_11_64 = 'WINDOWS_11_64'
    WINDOWS_10_32 = 'WINDOWS_10_32'
    WINDOWS_10_64 = 'WINDOWS_10_64'
    WINDOWS_8_64 = 'WINDOWS_8_64'
    WINDOWS_7_64 = 'WINDOWS_7_64'
    WINDOWS_7_32 = 'WINDOWS_7_32'
    WIN_SERVER_2016 = 'WIN_SERVER_2016'
    WIN_SERVER_2019 = 'WIN_SERVER_2019'
    CENTOS_6 = 'CENTOS_6'
    CENTOS_7 = 'CENTOS_7'
    CENTOS_8 = 'CENTOS_8'
    CENTOS_8_1 = 'CENTOS_8_1'
    UBUNTU_16 = 'UBUNTU_16'
    UBUNTU_18 = 'UBUNTU_18'
    UBUNTU_20 = 'UBUNTU_20'
