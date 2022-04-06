from infra.rest.rest_commands import RestCommands
from infra.system_components.collector import Collector


class Tenant:

    def __init__(self,
                 management_host_ip: str,
                 user_name: str,
                 user_password: str,
                 registration_password: str,
                 organization: str,
                 collector: Collector | None,
                 collector_group: str = "Default Collector Group"):

        self._user_name = user_name
        self._user_password = user_password
        self._registration_password = registration_password
        self._organization = organization
        self._collector_group = collector_group
        self._collector = collector
        self._rest_api_client = RestCommands(management_ip=management_host_ip,
                                             management_user=user_name,
                                             management_password=user_password,
                                             organization=organization)

    @property
    def user_name(self) -> str:
        return self._user_name

    @property
    def user_password(self) -> str:
        return self._user_password

    @property
    def registration_password(self) -> str:
        return self._registration_password

    @property
    def organization(self) -> str:
        return self._organization

    @property
    def collector(self) -> Collector:
        return self._collector

    @collector.setter
    def collector(self, collector: Collector):
        self._collector = collector

    @property
    def collector_group(self):
        return self._collector_group

    @property
    def rest_api_client(self) -> RestCommands:
        return self._rest_api_client

