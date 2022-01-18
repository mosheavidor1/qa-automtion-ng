from infra.enums import OsTypeEnum
from infra.os_stations.linux_station import LinuxStation
from infra.os_stations.os_station_base import OsStation
from infra.os_stations.windows_station import WindowsStation


class OsStationFactory:

    @staticmethod
    def get_os_station_according_to_type(os_type: OsTypeEnum,
                                         host_ip: str,
                                         user_name: str,
                                         password: str,
                                         encrypted_connection: bool = True) -> OsStation:

        if os_type == OsTypeEnum.WINDOWS:
            return WindowsStation(host_ip=host_ip,
                                  user_name=user_name,
                                  password=password,
                                  encrypted_connection=encrypted_connection)

        elif os_type == OsTypeEnum.LINUX or os_type == OsTypeEnum.OS_X:
            return LinuxStation(host_ip=host_ip,
                                user_name=user_name,
                                password=password)

        else:
            raise Exception(f"Unknown OS type: {os_type}")

