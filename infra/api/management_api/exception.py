import logging
import allure
from typing import List
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
logger = logging.getLogger(__name__)


class ExceptionFieldsNames(Enum):
    """ Exception's fields names as we get from server """
    ID = 'exceptionId'
    COLLECTORS_GROUPS = 'selectedCollectorGroups'
    DESTINATIONS = 'selectedDestinations'
    USERS = 'selectedUsers'
    COMMENT = 'comment'
    ORGANIZATION = 'organization'
    USERNAME = 'userName'
    UPDATED_AT = 'updatedAt'
    CREATED_AT = 'createdAt'
    EVENT_ID = 'originEventId'


class ExceptionManager(BaseApiObj):
    """ A wrapper of our internal rest client for working with Management Exceptions.
        Each Exception will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._id = initial_data[ExceptionFieldsNames.ID.value]  # Static, unique identifier

    def __repr__(self):
        return f"Management exception {self.id} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def id(self) -> int:
        return self._id

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = ExceptionFieldsNames.ORGANIZATION.value
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
    @allure.step("Create Exception")
    def create(cls, rest_client: RestCommands, event_id: int, organization_name, groups=None,
               expected_status_code=200, **kwargs):
        """ Create exception for event """
        logger.info(f"Create exception for event {event_id} in organization {organization_name}")
        existing_exceptions_fields = _get_exceptions_fields(rest_client=rest_client)
        exceptions_ids = [exception[ExceptionFieldsNames.ID.value] for exception in existing_exceptions_fields]

        destinations = kwargs.get("destinations", None)
        use_any_path = kwargs.get("useAnyPath", None)
        use_in_exception = kwargs.get("useInException", None)
        wild_card_files = kwargs.get("wildcardFiles", None)
        wild_card_paths = kwargs.get("wildcardPaths", None)

        params = {
            "eventId": event_id,
            "allCollectorGroups": False if groups is not None else True,
            "allDestinations": False if destinations is not None else True,
            "organization": organization_name,
            "allOrganizations": False if organization_name is not None else True
        }
        if groups is not None:
            params["collectorGroups"] = groups
        if destinations is not None:
            params["destinations"] = destinations

        body = {}
        if use_any_path is not None:
            body["useAnyPath"] = use_any_path
        if use_in_exception is not None:
            body["useInException"] = use_in_exception
        if wild_card_files is not None:
            body["wildcardFiles"] = wild_card_files
        if wild_card_paths is not None:
            body["wildcardPaths"] = wild_card_paths

        rest_client.exceptions.create_exception(params=params, body=body)
        updated_exceptions_fields = _get_exceptions_fields(rest_client=rest_client)
        exceptions_updated_ids = [exception[ExceptionFieldsNames.ID.value] for exception in updated_exceptions_fields]
        assert len(exceptions_updated_ids) - len(exceptions_ids) == 1, "New exception was not created"
        logger.debug("Find our new exception data and create obj that hold this data")
        for exception_fields in updated_exceptions_fields:
            if exception_fields[ExceptionFieldsNames.ID.value] not in exceptions_ids:
                new_exception_data = exception_fields
                break
        if expected_status_code == 200:
            _validate_new_exception_data(expected_organization_name=organization_name, expected_event_id=event_id,
                                         actual_data=new_exception_data)
        exception = cls(rest_client=rest_client, initial_data=new_exception_data)
        return exception

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        exceptions_fields = rest_client.exceptions.get_exceptions()
        for exception_fields in exceptions_fields:
            if exception_fields[ExceptionFieldsNames.ID.value] == self.id:
                logger.debug(f"{self} updated data from management: \n {exception_fields}")
                if update_cache_data:
                    self.cache = exception_fields
                return exception_fields
        assert safe, f"Exception with id {self.id} was not found"
        logger.debug(f"Exception with id {self.id} was not found")
        return None

    @allure.step("Delete Exception")
    def delete(self):
        """ Delete exception from management using user credentials """
        self._delete()

    def _delete(self, expected_status_code=200):
        logger.info(f"Delete {self}")
        self._rest_client.exceptions.delete_exception(self.id)
        if expected_status_code == 200:
            assert self.get_fields(safe=True) is None, f"{self} was not deleted"

    def update_fields(self, safe=False):
        raise NotImplemented("Should be implemented")


def _get_exceptions_fields(rest_client: RestCommands) -> List[dict]:
    exceptions_fields = rest_client.exceptions.get_exceptions()
    return exceptions_fields


def _validate_new_exception_data(expected_organization_name, expected_event_id, actual_data: dict):
    assert actual_data[ExceptionFieldsNames.EVENT_ID.value] == expected_event_id
    assert actual_data[ExceptionFieldsNames.ORGANIZATION.value] == expected_organization_name
