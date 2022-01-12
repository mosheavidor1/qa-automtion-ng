from infra.containers.system_component_containers import CoreDetails
from infra.enums import ComponentType
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation


class Core(FortiEdrLinuxStation):

    def __init__(self,
                 host_ip: str,
                 core_details: CoreDetails,
                 ssh_user_name: str = 'root',
                 ssh_password: str = 'enSilo$$'):
        super().__init__(host_ip=host_ip,
                         user_name=ssh_user_name,
                         password=ssh_password,
                         component_type=ComponentType.CORE)
        self._details = core_details

    def __repr__(self):
        return f"Core  {self._host_ip}"

    @property
    def details(self) -> CoreDetails:
        return self._details

    @details.setter
    def details(self, details: CoreDetails):
        self._details = details

    def get_logs_folder_path(self):
        return "/opt/FortiEDR/core/Logs/Core"
