from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.collector_group import CollectorGroup, GroupFieldsNames
import logging
import allure
from typing import List
logger = logging.getLogger(__name__)


class GroupsFactory(BaseApiObjFactory):
    """ Find/Create groups in the given organization and return them as rest objects """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_name(self, name: str, safe=False) -> CollectorGroup:
        """ Find group by name and return its rest api wrapper """
        groups = self.get_by_field(field_name=GroupFieldsNames.NAME.value, value=name)
        if groups is None:
            assert safe, f"Org '{self._organization_name}' doesn't contain group {name}"
            logger.debug(f"Org '{self._organization_name}' doesn't contain group {name}")
            return None
        assert len(groups) == 1, f"These groups have same name ! : \n {groups}"
        return groups[0]

    def get_by_field(self, field_name, value) -> List[CollectorGroup]:
        """ Get groups by field """
        groups = []
        org_name = self._organization_name
        logger.debug(f"Find groups with field {field_name} = {value} in org: '{org_name}'")
        all_groups_fields = self._factory_rest_client.system_inventory.get_collector_groups(organization_name=org_name)
        for group_fields in all_groups_fields:
            if group_fields[field_name] == value:
                group = CollectorGroup(rest_client=self._factory_rest_client, initial_data=group_fields)
                groups.append(group)
        if len(groups):
            logger.info(f"Found these groups with field {field_name}={value}: \n {groups}")
            return groups
        logger.debug(f"Groups with field {field_name}={value} were not found in {org_name}")
        return None

    @allure.step("Create collector group")
    def create_collector_group(self, group_name, expected_status_code=200) -> CollectorGroup:
        """ Create new collector group """
        logger.info(f"Create new collector group with name {group_name} in organization {self._organization_name}")
        group = CollectorGroup.create(rest_client=self._factory_rest_client, name=group_name,
                                      organization_name=self._organization_name,
                                      expected_status_code=expected_status_code)
        return group
