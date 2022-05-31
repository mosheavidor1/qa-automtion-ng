from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.system_components.collector import CollectorAgent
from infra.api.api_objects_factory import RestCollectorsFactory


class Tenant:

    def __init__(self,
                 management_host_ip: str,
                 user_name: str,
                 user_password: str,
                 registration_password: str,
                 organization: str,
                 collector: CollectorAgent | None,
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
        self.rest_components: TenantRestComponents = TenantRestComponents(organization_name=organization,
                                                                          rest_client=self._rest_api_client)

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
    def collector(self) -> CollectorAgent:
        return self._collector

    @collector.setter
    def collector(self, collector: CollectorAgent):
        self._collector = collector

    @property
    def collector_group(self):
        return self._collector_group

    @property
    def rest_api_client(self) -> RestCommands:
        return self._rest_api_client


class TenantRestComponents:
    def __init__(self, organization_name: str, rest_client: RestCommands):
        self._organization_name = organization_name
        self.collectors: RestCollectorsFactory = RestCollectorsFactory(organization_name=organization_name,
                                                                       rest_client=rest_client)
