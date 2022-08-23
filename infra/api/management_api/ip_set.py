import copy
import time
from typing import List

import allure
from enum import Enum

from deepdiff import DeepDiff

from infra.api.api_object import BaseApiObj, logger
from infra.api.nslo_wrapper.rest_commands import RestCommands


WAIT_AFTER_CREATE_IP_SET = 60


class IpSetFieldsNames(Enum):
    """ Ip set's fields names as we get from server """

    NAME = 'name'
    ORGANIZATION = 'organization'
    INCLUDE = 'include'
    EXCLUDE = 'exclude'
    DESCRIPTION = 'description'


class IpSet(BaseApiObj):
    """ A wrapper of our internal rest client for working with ip set capabilities.
    Each ip set will have its own rest credentials based on user password and name (that passed from users factory)"""

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._name = initial_data[IpSetFieldsNames.NAME.value]  # Static, unique identifier

    def __repr__(self):
        return f"Ip set {self.name} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def name(self) -> str:
        return self._name

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = IpSetFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_include(self, from_cache=None, update_cache=True):
        field_name = IpSetFieldsNames.INCLUDE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_exclude(self, from_cache=None, update_cache=True):
        field_name = IpSetFieldsNames.EXCLUDE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_description(self, from_cache=None, update_cache=True):
        field_name = IpSetFieldsNames.DESCRIPTION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def _get_field(self, field_name, from_cache, update_cache):
        from_cache = from_cache if from_cache is not None else self._use_cache
        if from_cache:
            value = self._cache[field_name]
        else:
            updated_value = self.get_fields()[field_name]
            value = updated_value
            if update_cache:
                self._cache[field_name] = updated_value
        return value

    @classmethod
    @allure.step("Create IpSet")
    def create(cls, rest_client: RestCommands, name, organization, include, exclude: None, description: None,
               expected_status_code=200):
        """ Create IpSet
        Optional data: excludeIPs, description """

        logger.info(f"Create new ip set '{name}' in organization {organization}")
        ip_set_data = {
            # IpSetFieldsNames.NAME.value: name,
            IpSetFieldsNames.ORGANIZATION.value: organization,
            IpSetFieldsNames.INCLUDE.value: include,
            IpSetFieldsNames.EXCLUDE.value: exclude,
            IpSetFieldsNames.DESCRIPTION.value: description,
        }
        rest_client.ip_sets.define_new_ip_set(name=name, ip_set_data=ip_set_data)
        time.sleep(WAIT_AFTER_CREATE_IP_SET)
        new_ip_set_data = get_ip_set_fields_by_name(rest_client=rest_client, name=name,
                                                    organization=organization, safe=False)
        if expected_status_code == 200:
            ip_set = cls(rest_client=rest_client, initial_data=new_ip_set_data)
        return ip_set

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        ip_sets_fields = rest_client.ip_sets.get_ip_sets()
        for ip_set_fields in ip_sets_fields:
            if ip_set_fields[IpSetFieldsNames.NAME.value] == self.name:
                logger.debug(f"{self} updated data from management: \n {ip_set_fields}")
                if update_cache_data:
                    self.cache = ip_set_fields
                return ip_set_fields
        assert safe, f"ip set with name {self.name} was not found"
        logger.debug(f"ip set with name {self.name} was not found")
        return None

    @allure.step("Delete Ip set")
    def delete(self):
        """ Delete ip set from management """
        self._delete()

    def _delete(self, expected_status_code=200):
        logger.info(f"Delete {self}")
        self._rest_client.ip_sets.delete_ip_set(name=self.name, organization=self.get_organization_name())
        if expected_status_code == 200:
            assert self.get_fields(safe=True) is None, f"{self} was not deleted"

    def update_fields(self, include: List[str], exclude: List[str] = None, description: str = None,
                      expected_status_code: int = 200):
        """ Update IpSet
            Optional data: excludeIPs, description """
        org_name = self.get_organization_name(from_cache=False)
        self.update_all_cache()

        logger.info(f"update exist ip set '{self._name}' in organization {org_name}")
        expected_data = copy.deepcopy(self.cache)

        if include is not None:
            expected_data[IpSetFieldsNames.INCLUDE.value] = include
        if exclude is not None:
            expected_data[IpSetFieldsNames.EXCLUDE.value] = exclude
        if description is not None:
            expected_data[IpSetFieldsNames.DESCRIPTION.value] = description

        updated_data = copy.deepcopy(expected_data)
        del updated_data[IpSetFieldsNames.NAME.value]

        self._rest_client.ip_sets.update_exist_ip_set(name=self._name,
                                                      ip_set_data=updated_data,
                                                      expected_status_code=200)

        if expected_status_code == 200:
            self.update_all_cache()
            delta = DeepDiff(self.cache, expected_data, ignore_order=False, report_repetition=True)
            assert len(delta) == 0, f"There is a mismatch between the expected: {expected_data} and actual {self.cache}"


def get_ip_set_fields_by_name(rest_client: RestCommands, name, organization, safe=False) -> dict:
    """ When creating new Ip set the response doesn't contain any data, only status code, use this to get the
        rest data in order to initialize the ip set instance """
    ip_sets_fields = rest_client.ip_sets.get_ip_sets()
    for ip_set_fields in ip_sets_fields:
        if ip_set_fields[IpSetFieldsNames.NAME.value] == name:
            logger.debug(f"Ip set '{name}' updated data from management: \n {ip_set_fields}")
            return ip_set_fields
    assert safe, f"ip set {name} was not found in organization {organization}"
    logger.debug(f"ip set {name} was not found in organization {organization}")
    return None











