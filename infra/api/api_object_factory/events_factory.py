import allure
from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.event import Event, EventFieldsNames, WAIT_AFTER_DELETE
from infra import common_utils
import logging
import functools
from typing import List
import time

from infra.common_utils import WAIT_FOR_COLLECTOR_NEW_CONFIGURATION

logger = logging.getLogger(__name__)

MAX_WAIT_FOR_EVENT = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
GET_EVENT_INTERVAL = 2


class EventsFactory(BaseApiObjFactory):
    """ Find/Create events and return them as rest objects  with the user's credentials.
    The factory's rest credentials will be set as the default auth of each of the returned
    event objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_all(self, rest_client=None, safe=False) -> List[Event]:
        events = []
        rest_client = rest_client or self._factory_rest_client
        logger.debug(f"Find all Events in organization {self._organization_name}")
        all_events_fields = rest_client.events.get_events()
        for event_fields in all_events_fields:
            event = Event(rest_client=rest_client, initial_data=event_fields)
            events.append(event)
        if len(events):
            return events
        assert safe, f"Didn't find any event in organization {self._organization_name}"
        logger.info(f"Didn't find any event in organization {self._organization_name}")
        return events

    def get_by_process_name(self, process_name, rest_client=None, safe=False,
                            wait_for=False, timeout=None, interval=None) -> List[Event]:
        field_name = EventFieldsNames.PROCESS_NAME.value
        events = self._get_events_by_field(field_name=field_name, value=process_name, rest_client=rest_client,
                                           safe=safe, wait_for=wait_for, timeout=timeout, interval=interval)
        return events

    def _get_events_by_field(self, field_name, value, rest_client=None, safe=False, wait_for=False,
                             timeout=None, interval=None) -> List[Event]:
        """ Find events by field name<>value and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        rest_client = rest_client or self._factory_rest_client
        get_event_func = functools.partial(self.get_by_field, field_name=field_name,
                                           value=value, rest_client=rest_client)
        if wait_for:
            _wait_for_event(get_event_func=get_event_func, timeout=timeout, interval=interval, safe=safe)
        events = get_event_func(safe=safe)
        return events

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> List[Event]:
        events = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find events with field {field_name} = {value} in organization {org_name}")
        events_fields = rest_client.events.get_events(**{field_name: value})
        for event_fields in events_fields:
            event = Event(rest_client=rest_client, initial_data=event_fields)
            events.append(event)
        if len(events):
            logger.debug(f"Found these events with field {field_name}={value}: \n {events}")
            return events
        assert safe, f"Didn't find any event with field {field_name}={value} in organization {self._organization_name}"
        logger.info(f"Didn't find any event with field {field_name}={value} in organization {self._organization_name}")
        return events

    @allure.step("Delete all Events")
    def delete_all(self, rest_client=None, safe: bool = False, wait_sec: int = None):
        wait_sec = wait_sec or WAIT_AFTER_DELETE
        logger.info(f"Delete events in organization {self._organization_name} and wait {wait_sec} seconds")
        rest_client = rest_client or self._factory_rest_client
        all_events = self.get_all(rest_client=rest_client, safe=safe)
        for event in all_events:
            logger.info(f"Delete {event} from organization {self._organization_name}")
            event.delete()
        if len(all_events):
            logger.info(f"Sleep {wait_sec} sec, this is the period of time that took for deletion in the backend")
            time.sleep(wait_sec)
        remaining_events = self.get_all(rest_client=rest_client, safe=safe)
        assert len(remaining_events) == 0, f"These events were not deleted: {remaining_events}"


def _wait_for_event(get_event_func, timeout=None, interval=None, safe=False):
    timeout = timeout or MAX_WAIT_FOR_EVENT
    interval = interval or GET_EVENT_INTERVAL

    def condition():
        return True if get_event_func(safe=True) else False
    try:
        common_utils.wait_for_condition(condition_func=condition, timeout_sec=timeout, interval_sec=interval,
                                        condition_msg="Wait for specific event")
    except AssertionError:
        if not safe:
            raise Exception(f"Error - No event found after waiting {timeout} seconds")


