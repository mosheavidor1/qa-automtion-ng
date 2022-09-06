from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.collector import CollectorFieldsNames, RestCollector
import logging
from infra.api import ADMIN_REST
logger = logging.getLogger(__name__)


class RestCollectorsFactory(BaseApiObjFactory):
    """ 1. Collectors can't be created via rest api, so find real collectors in the given organization and return
        them as rest objects.
        2. The factory's rest credentials will be set as the default auth of each of the returned
        collector objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_ip(self, ip: str, rest_client=None, safe=False) -> RestCollector:
        """ Find real collector by ip and return its rest api wrapper,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        rest_client = rest_client or self._factory_rest_client
        rest_collectors = self.get_by_field(field_name=CollectorFieldsNames.IP.value, value=ip,
                                            rest_client=rest_client, safe=safe)
        rest_collectors = [] if rest_collectors is None else rest_collectors
        if len(rest_collectors):
            assert len(rest_collectors) == 1, f"These collectors have same ip ! \n {rest_collectors}"
            return rest_collectors[0]
        assert safe, f"collectors with ip {ip} were not found in {self._organization_name}"
        logger.debug(f"collectors with ip {ip} were not found in {self._organization_name}")
        return None

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> RestCollector:
        rest_client = rest_client or self._factory_rest_client
        collectors = []
        org_name = self._organization_name
        logger.debug(f"Find collectors with field {field_name} = {value} in {org_name}")
        all_collectors = self.get_all(rest_client=rest_client, safe=safe)
        all_collectors = [] if all_collectors is None else all_collectors
        for collector in all_collectors:
            if collector.cache[field_name] == value:
                collectors.append(collector)
        logger.debug(f"Found collectors: {collectors}")
        if len(collectors):
            return collectors
        assert safe, f"collectors with field {field_name}={value} were not found in {org_name}"
        logger.debug(f"collectors with field {field_name}={value} were not found in {org_name}")
        return None

    def get_all(self, rest_client=None, safe=False):
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find all rest collectors in organization {org_name}")
        rest_collectors = []
        all_collectors_fields = rest_client.system_inventory.get_collector_info(organization=org_name)
        for collector_fields in all_collectors_fields:
            rest_collector = RestCollector(rest_client=rest_client, initial_data=collector_fields)
            rest_collectors.append(rest_collector)
        if len(rest_collectors):
            return rest_collectors
        assert safe, f"Org '{org_name}' doesn't contain collectors"
        logger.debug(f"Org '{org_name}' doesn't contain collectors")
        return None

    def create(self):
        raise NotImplemented("Collector can't be created via rest")


def get_collectors_without_org(safe=True):
    """ Return collectors that don't have organization, the returned collectors have admin credentials because
        they are under admin user (no organization) """
    logger.debug(f"Find all rest collectors that don't have organizations")
    collectors_factory = RestCollectorsFactory(organization_name=None, factory_rest_client=ADMIN_REST())
    rest_collectors = collectors_factory.get_all(safe=safe)
    return rest_collectors
