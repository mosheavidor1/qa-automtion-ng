from datetime import datetime
from enum import Enum
from infra.api.api_object import BaseApiObj, logger
from infra.api.nslo_wrapper.rest_commands import RestCommands


class SystemEventsFieldsNames(Enum):
    COMPONENT_NAME = 'componentName'
    COMPONENT_TYPE = 'componentType'
    DATE = 'date'
    DESCRIPTION = 'description'
    ORGANIZATION = 'organization'


class SystemEvent(BaseApiObj):
    """ A wrapper of our internal rest client for working with system event.
           Each event will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._name = initial_data[SystemEventsFieldsNames.COMPONENT_NAME.value]
        self._date = initial_data[SystemEventsFieldsNames.DATE.value]  # Static, unique identifier

    def __repr__(self):
        return f"System event {self.name} in '{self.get_organization_name(from_cache=True)}'"

    @property
    def name(self) -> str:
        return self._name

    @property
    def date(self) -> str:
        return self._date

    def get_organization_name(self, from_cache=None, update_cache=True) -> str:
        field_name = SystemEventsFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_date(self, from_cache=None, update_cache=True) -> datetime:
        field_name = SystemEventsFieldsNames.DATE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        value_convert_to_time = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value_convert_to_time

    def get_component_type(self, from_cache=None, update_cache=True) -> str:
        field_name = SystemEventsFieldsNames.COMPONENT_TYPE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_description(self, from_cache, update_cache=False) -> str:
        field_name = SystemEventsFieldsNames.DESCRIPTION.value
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

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        system_events_fields = rest_client.system_events.get_system_events()
        for system_event_fields in system_events_fields:
            if system_event_fields[SystemEventsFieldsNames.COMPONENT_NAME.value] == self.name and \
                    system_event_fields[SystemEventsFieldsNames.DATE.value] == self.date:
                logger.debug(f"{self} updated data from management: \n {system_event_fields}")
                if update_cache_data:
                    self.cache = system_event_fields
                return system_event_fields
        assert safe, f"system event with name {self.name} and date {self.date} was not found"
        logger.debug(f"system event with name {self.name} and date {self.date} was not found")
        return None

    def update_fields(self, safe=False):
        pass

    @classmethod
    def create(cls):
        pass

    def _delete(self):
        pass














