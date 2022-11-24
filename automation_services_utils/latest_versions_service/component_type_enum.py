from enum import Enum


class ComponentTypeEnum(Enum):
    MANAGER = "manager"
    AGGREGATOR = "aggregator"
    CORE = "core"
    WINDOWS_COLLECTOR = "windows_collector"
    LINUX_COLLECTOR = "linux_collector"
