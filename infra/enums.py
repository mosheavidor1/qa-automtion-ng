from enum import Enum


class UserRoles(Enum):
    USER = 'User'
    ADMIN = 'Admin'
    LOCAL_ADMIN = 'Local Admin'
    REST_API = 'Rest API'


class SystemState(Enum):
    RUNNING = 'RUNNING'
    NOT_RUNNING = 'NOT_RUNNING'
    DISCONNECTED = 'DISCONNECTED'
    DOWN = 'DOWN'


class ComponentType(Enum):
    MANAGEMENT = 'manager'
    BOTH = 'both'
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
    LINUX_CENTOS_6 = 'LINUX_CENTOS_6'
    LINUX_CENTOS_7 = 'LINUX_CENTOS_7'
    LINUX_CENTOS_8 = 'LINUX_CENTOS_8'
    LINUX_UBUNTU_16 = 'LINUX_UBUNTU_16'
    LINUX_UBUNTU_18 = 'LINUX_UBUNTU_18'
    LINUX_UBUNTU_20 = 'LINUX_UBUNTU_20'


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

