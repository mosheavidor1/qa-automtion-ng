from infra.containers.system_component_containers import AggregatorDetails
from infra.enums import ComponentType
from infra.system_components.forti_edr_linux_station import FortiEdrLinuxStation


class Aggregator(FortiEdrLinuxStation):

    def __init__(self,
                 host_ip: str,
                 aggregator_details: AggregatorDetails | None,
                 ssh_user_name: str = 'root',
                 ssh_password: str = 'enSilo$$'):

        super().__init__(host_ip=host_ip,
                         user_name=ssh_user_name,
                         password=ssh_password,
                         component_type=ComponentType.AGGREGATOR)
        self._details = aggregator_details

    def __repr__(self):
        return f"Aggregator  {self._host_ip}"

    @property
    def details(self) -> AggregatorDetails:
        return self._details

    @details.setter
    def details(self, details: AggregatorDetails):
        self._details = details

    def get_logs_folder_path(self):
        return '/opt/FortiEDR/aggregator/tmp'
