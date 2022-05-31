from abc import abstractmethod
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
import sut_details

logger = logging.getLogger(__name__)


class BaseApiObj:
    """ Abstract class for working with objects that are api wrappers """
    admin_rest = RestCommands(sut_details.management_host, sut_details.management_ui_admin_user_name,
                              sut_details.management_ui_admin_password)

    def __init__(self, rest_client):
        self._rest_client = rest_client

    @property
    def rest_client(self) -> RestCommands:
        return self._rest_client

    @classmethod
    @abstractmethod
    def create(cls):
        """ A class factory that create the object in management via api calls """
        pass

    @abstractmethod
    def get_fields(self, safe=False):
        """ Get object's fields from management , raise exception if not found """
        pass

    @abstractmethod
    def update(self, safe=False):
        """ Update object's fields in management , raise exception if not found """
        pass

    @abstractmethod
    def delete(self):
        """ Delete object from management """
        pass

    def is_exist(self) -> bool:
        """ Check if object exists in management """
        logger.info(f"Check if {self} exists")
        return self.get_fields(safe=True) is not None

    def validate_creation(self, expected_status_code):
        """ Validate that api call really worked: created the object"""
        is_created = self.is_exist()
        if expected_status_code == 200:
            assert is_created, f"Api returned OK but actually {self} was NOT created"

    def validate_deletion(self, expected_status_code):
        """ Validate that api call really worked: deleted the object"""
        is_deleted = not self.is_exist()
        if expected_status_code == 200:
            assert is_deleted, f"Api returned OK but actually {self} was NOT deleted"

    def validate_update(self, fields_new_values: List[tuple], expected_status_code):
        """ Validate that api call really worked: updated the object's field"""
        updated_fields = self.get_fields()
        for field_name, expected_value in fields_new_values:
            if expected_status_code == 200:
                assert updated_fields[field_name] == expected_value, \
                    f"Api returned OK but actually {field_name} was NOT updated"
