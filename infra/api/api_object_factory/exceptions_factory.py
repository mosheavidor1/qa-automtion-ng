import allure
from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.exception import ExceptionManager, ExceptionFieldsNames
import logging
from typing import List
import time
logger = logging.getLogger(__name__)


class ExceptionsFactory(BaseApiObjFactory):
    """ Find/Create Management exceptions and return them as rest objects  with the user's credentials.
    The factory's rest credentials will be set as the default auth of each of the returned
    exception objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_all(self, rest_client=None, safe=False) -> List[ExceptionManager]:
        exceptions = []
        rest_client = rest_client or self._factory_rest_client
        logger.debug(f"Find all Exceptions in organization {self._organization_name}")
        all_exceptions_fields = rest_client.exceptions.get_exceptions()
        for exception_fields in all_exceptions_fields:
            exception = ExceptionManager(rest_client=rest_client, initial_data=exception_fields)
            exceptions.append(exception)
        if len(exceptions):
            return exceptions
        assert safe, f"Didn't find any exception in organization {self._organization_name}"
        logger.info(f"Didn't find any exception in organization {self._organization_name}")
        return exceptions

    def get_by_event_id(self, event_id: int, rest_client=None, safe=False) -> List[ExceptionManager]:
        """ Find exceptions by event id and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        event_exceptions = []
        rest_client = rest_client or self._factory_rest_client
        logger.debug(f"Find all Exceptions in organization {self._organization_name} that related to event {event_id}")
        event_exceptions_fields = rest_client.exceptions.get_exceptions(event_id=event_id)
        for exception_fields in event_exceptions_fields:
            exception = ExceptionManager(rest_client=rest_client, initial_data=exception_fields)
            event_exceptions.append(exception)
        if len(event_exceptions):
            return event_exceptions
        assert safe, f"Didn't find any exception for event {event_id} in organization {self._organization_name}"
        logger.debug(f"Didn't find any exception for event {event_id} in organization {self._organization_name}")
        return None

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> ExceptionManager:
        raise NotImplemented("Should be implemented")

    @allure.step("Delete all Exceptions")
    def delete_all(self, rest_client=None, safe=False, wait_sec=60):
        logger.info(f"Delete exceptions in organization {self._organization_name} and wait {wait_sec} seconds")
        rest_client = rest_client or self._factory_rest_client
        all_exceptions = self.get_all(rest_client=rest_client, safe=safe)
        for exception in all_exceptions:
            logger.info(f"Delete {exception} from organization {self._organization_name}")
            exception.delete()
        if len(all_exceptions):
            time.sleep(wait_sec)
            remaining_exceptions = self.get_all(rest_client=rest_client, safe=safe)
            assert len(remaining_exceptions) == 0, f"These exceptions were not deleted: {remaining_exceptions}"

    def create_exception_for_event(self, event_id, groups=None, expected_status_code=200, **kwargs) -> ExceptionManager:
        """ Create new exception """
        logger.info(f"Create new exception for event {event_id} in organization {self._organization_name}")
        exception = ExceptionManager.create(rest_client=self._factory_rest_client, event_id=event_id,
                                            organization_name=self._organization_name, groups=groups,
                                            expected_status_code=expected_status_code, **kwargs)
        return exception
