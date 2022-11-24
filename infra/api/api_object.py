from abc import abstractmethod
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
from infra.api import ADMIN_REST

logger = logging.getLogger(__name__)


class BaseApiObj:
    """ Abstract class for working with objects that are api wrappers of real components """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        self._rest_client: RestCommands = rest_client
        self._cache = initial_data
        self._use_cache = False  # By default, always get the updated data from server

    @property
    def cache(self) -> dict:
        return self._cache

    @cache.setter
    def cache(self, new_cache: dict):
        self._cache = new_cache

    @property
    def use_cache(self) -> bool:
        return self._use_cache

    @use_cache.setter
    def use_cache(self, to_use: bool):
        self._use_cache = to_use

    @classmethod
    @abstractmethod
    def create(cls):
        """ Create new component in management (via api) and return this component's rest api wrapper """
        pass

    @abstractmethod
    def get_fields(self, safe=False, rest_client=None):
        """ Get object's fields from management by id, raise exception if not found """
        pass

    @abstractmethod
    def update_fields(self, safe=False):
        """ Update object's fields in management , raise exception if not found """
        pass

    @abstractmethod
    def _delete(self):
        """ Private because there are objects that need higher credentials for deletion (like users,
        should not present public delete method, users deleted via tenant credentials: 'tenant.delete_user()') """
        pass

    def is_exist(self) -> bool:
        """ Check if object exists in management """
        logger.info(f"Check if {self} exists")
        return self.get_fields(safe=True, rest_client=ADMIN_REST()) is not None

    def _validate_deletion(self):
        """ Validate that api call really worked: deleted the object"""
        is_deleted = not self.is_exist()
        assert is_deleted, f"Api returned OK but actually {self} was NOT deleted"

    def update_all_cache(self):
        """ Update all cached fields with new values from server"""
        self.get_fields(update_cache_data=True)

    def _validate_updated_fields(self, new_fields: List[tuple]):
        self.update_all_cache()
        current_data = self.cache
        for field_name, new_value in new_fields:
            assert current_data[field_name] == new_value, \
                f"{field_name} is {current_data[field_name]} instead of {new_value}"
