import logging
import allure
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
logger = logging.getLogger(__name__)

WAIT_FOR_COLLECTOR_NEW_CONFIGURATION = 60  # The period of time that took for deletion in the backend - non-configurable configuration


class EventFieldsNames(Enum):
    """ Event's fields names as we get from server """
    ID = 'eventId'
    THREAT_DETAILS = 'threatDetails'
    SEVERITY = 'severity'
    SEEN = 'seen'
    RULES = 'rules'
    ORGANIZATION = 'organization'
    PROCESS_NAME = 'process'
    ACTION = 'action'


class EventActionNames (Enum):
    SIMULATION_BLOCK ="SimulationBlock"
    BLOCK = "Block"


class Event(BaseApiObj):
    """ A wrapper of our internal rest client for working with Events.
        Each Event will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._id = initial_data[EventFieldsNames.ID.value]  # Static, unique identifier

    def __repr__(self):
        return f"Event {self.id} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def id(self) -> int:
        return self._id

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = EventFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_rules(self, from_cache=None, update_cache=True):
        field_name = EventFieldsNames.RULES.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_process_name(self, from_cache=None, update_cache=True):
        field_name = EventFieldsNames.PROCESS_NAME.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_action(self, from_cache=None, update_cache=True):
        field_name = EventFieldsNames.ACTION.value
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

    def create(self):
        raise NotImplemented("Event can't be created via management, only from the collector agent")

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        events_fields = rest_client.events.get_events()
        for event_fields in events_fields:
            if event_fields[EventFieldsNames.ID.value] == self.id:
                logger.debug(f"{self} updated data from management: \n {event_fields}")
                if update_cache_data:
                    self.cache = event_fields
                return event_fields
        assert safe, f"Event with id {self.id} was not found"
        logger.debug(f"Event with id {self.id} was not found")
        return None

    @allure.step("Delete Event")
    def delete(self):
        """ Delete event from management using user credentials """
        self._delete()

    def _delete(self, expected_status_code=200):
        logger.info(f"Delete {self}")
        self._rest_client.events.delete_events(event_ids=[self.id])
        if expected_status_code == 200:
            assert self.get_fields(safe=True) is None, f"{self} was not deleted"

    def update_fields(self, safe=False):
        raise NotImplemented("Should be implemented")
