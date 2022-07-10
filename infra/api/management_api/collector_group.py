import logging
import allure
from typing import List
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
logger = logging.getLogger(__name__)


class GroupFieldsNames(Enum):
    """ Group's fields names as we get from server """
    ID = 'id'
    NAME = 'name'
    ORGANIZATION = 'organization'


class CollectorGroup(BaseApiObj):
    """ A wrapper of our internal rest client for working with collector groups.
        Each group will have its own rest credentials based on user credentials """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._id = initial_data[GroupFieldsNames.ID.value]  # Static, unique identifier
        self._organization_name = initial_data[GroupFieldsNames.ORGANIZATION.value]
        self._name = initial_data[GroupFieldsNames.NAME.value]

    def __repr__(self):
        return f"Collector group {self.id} named '{self.name}'"

    @property
    def id(self) -> int:
        return self._id

    @property
    def organization_name(self):
        return self._organization_name

    @property
    def name(self):
        return self._name

    @classmethod
    @allure.step("Create Collector group")
    def create(cls, rest_client: RestCommands, name, organization_name, expected_status_code=200):
        logger.info(f"Create group with name {name} in organization {organization_name}")
        assert not is_exists_by_name(rest_client=rest_client, name=name, organization_name=organization_name), \
            f"Group with name {name} already exists"
        rest_client.system_inventory.create_group(name=name)
        new_group_data = get_group_fields_by_name(rest_client=rest_client, name=name,
                                                  organization_name=organization_name, safe=False)
        group = cls(rest_client=rest_client, initial_data=new_group_data)
        return group

    def get_fields(self, safe=False, update_cache_data=False, rest_client: RestCommands = None) -> dict:
        rest_client = rest_client or self._rest_client
        groups_fields = rest_client.system_inventory.get_collector_groups(organization_name=self.organization_name)
        for group_fields in groups_fields:
            if group_fields[GroupFieldsNames.ID.value] == self.id:
                logger.info(f"{self} updated data from management: \n {group_fields}")
                if update_cache_data:
                    self.cache = group_fields
                return group_fields
        assert safe, f"Group with id {self.id} and name {self.name} was not found"
        logger.debug(f"Group with id {self.id} and name {self.name} was not found")
        return None

    def _delete(self, expected_status_code=200):
        raise NotImplemented("Group can be deleted only via GUI (Testim)")

    def update_fields(self, safe=False):
        raise NotImplemented("Not relevant")


def get_group_fields_by_name(rest_client: RestCommands, name, organization_name, safe=False) -> dict:
    groups_fields = rest_client.system_inventory.get_collector_groups(organization_name=organization_name)
    for group_fields in groups_fields:
        if group_fields[GroupFieldsNames.NAME.value] == name:
            logger.info(f"Group '{name}' updated data from management: \n {group_fields}")
            return group_fields
    assert safe, f"Group {name} was not found in organization {organization_name}"
    logger.debug(f"Group {name} was not found in organization {organization_name}")
    return None


def is_exists_by_name(rest_client: RestCommands, name, organization_name):
    group_fields = get_group_fields_by_name(rest_client=rest_client, name=name,
                                            organization_name=organization_name, safe=True)
    if group_fields is None:
        return False
    else:
        return True

