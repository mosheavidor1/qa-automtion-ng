from abc import abstractmethod
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.collector import CollectorFieldsNames, RestCollector
import logging

logger = logging.getLogger(__name__)


class BaseApiObjFactory:
    """ Abstract base class for finding existing api objects or creating new ones """

    @abstractmethod
    def get_by_field(self, field_name, value):
        pass

    @abstractmethod
    def get_all(self, field_name, value):
        pass

    @abstractmethod
    def create(self):
        """ Create new mgmt api object """
        pass


class RestCollectorsFactory(BaseApiObjFactory):
    """ Creating/Finding management's api collectors objects """
    def __init__(self, organization_name: str, rest_client: RestCommands):
        self._organization_name = organization_name
        self._rest_client = rest_client

    def get_by_ip(self, ip: str, rest_client=None) -> RestCollector:
        """ Return existing collector from mgmt by ip """
        rest_client = rest_client or self._rest_client
        obj = self.get_by_field(field_name=CollectorFieldsNames.IP.value, value=ip, rest_client=rest_client)
        return obj

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> RestCollector:
        org_name = self._organization_name
        logger.info(f"Find collector with field {field_name} = {value} in {org_name}")
        rest_client = rest_client or self._rest_client
        all_collectors = self.get_all(rest_client=rest_client)
        for collector in all_collectors:
            if collector.cache[field_name] == value:
                logger.info(f"Found collector: {collector}")
                return collector
        if not safe:
            raise Exception(f"collector with field {field_name}={value} was not found in {org_name}")
        logger.warning(f"collector with field {field_name}={value} was not found in {org_name}")
        return None

    def get_all(self, rest_client=None, safe=False):
        """ Return all existing collectors objects in the organization"""
        org_name = self._organization_name
        logger.info(f"Find all rest collectors in {org_name}")
        rest_collectors = []
        rest_client = rest_client or self._rest_client
        all_collectors_fields = rest_client.system_inventory.get_collector_info(organization=org_name)
        for collector_fields in all_collectors_fields:
            rest_collector = RestCollector(rest_client=rest_client, initial_data=collector_fields)
            rest_collectors.append(rest_collector)
        if len(rest_collectors):
            return rest_collectors
        if not safe:
            raise Exception(f"Org '{org_name}' doesn't contain collectors")
        logger.warning(f"Org '{org_name}' doesn't contain collectors")
        return None

    def create(self):
        raise NotImplemented("Collector can't be created via rest")
