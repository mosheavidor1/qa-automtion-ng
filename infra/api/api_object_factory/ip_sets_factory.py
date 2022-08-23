import allure

from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.management_api.ip_set import IpSet, IpSetFieldsNames
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
logger = logging.getLogger(__name__)


class IpSetFactory(BaseApiObjFactory):

    """ Find policies and return them as rest objects  with the user's credentials.
       The factory's rest credentials will be set as the default auth of each of the returned
       policy objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_name(self, ip_set_name, rest_client=None, safe=False) -> IpSet:
        rest_client = rest_client or self._factory_rest_client
        field_name = IpSetFieldsNames.NAME.value
        ip_sets = self.get_by_field(field_name=field_name, value=ip_set_name, rest_client=rest_client, safe=safe)
        assert len(ip_sets) == 1
        return ip_sets[0]

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> List[IpSet]:
        """ Find ip sets by field name<>value and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        ip_sets = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find ip_sets with field {field_name} = {value} in organization {org_name}")
        ip_sets_fields = rest_client.ip_sets.get_ip_sets()
        for ip_set_fields in ip_sets_fields:
            if ip_set_fields[field_name] == value:
                ip_set = IpSet(rest_client=rest_client, initial_data=ip_set_fields)
                ip_sets.append(ip_set)
        if len(ip_sets):
            logger.debug(f"Found these ip sets with field {field_name}={value}: \n {ip_sets}")
            return ip_sets
        assert safe, f"Didn't find any ip set with field {field_name}={value} in organization {self._organization_name}"
        logger.info(f"Didn't find any ip set with field {field_name}={value} in organization {self._organization_name}")
        return None

    def get_all(self, rest_client=None, safe=False) -> List[IpSet]:
        ip_sets = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find all ip sets in organization {org_name}")
        ip_sets_fields = rest_client.ip_sets.get_ip_sets()
        for ip_set_fields in ip_sets_fields:
            ip_set = IpSet(rest_client=rest_client, initial_data=ip_set_fields)
            ip_sets.append(ip_set)
        if len(ip_sets):
            logger.debug(f"Found these ip sets: \n {ip_sets}")
            return ip_sets
        assert safe, f"Didn't find ip sets  in organization {self._organization_name}"
        logger.info(f"Didn't find ip sets in organization {self._organization_name}")
        return ip_sets

    @allure.step("Create Ip set with the name: {name} in the organization: {organization}")
    def create_ip_set(self, name: str, organization: int, include, exclude=None, description=None,
                      expected_status_code=200) -> IpSet:
        logger.info(f"Create ip set '{name}' in organization '{organization}'")
        ip_set = IpSet.create(name=name, organization=organization, rest_client=self._factory_rest_client,
                              include=include, exclude=exclude, description=description,
                              expected_status_code=expected_status_code)
        return ip_set
