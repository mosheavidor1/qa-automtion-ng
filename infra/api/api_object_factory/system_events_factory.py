from datetime import datetime
from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.management_api.system_events import SystemEvent, SystemEventsFieldsNames
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
logger = logging.getLogger(__name__)


class SystemEventsFactory(BaseApiObjFactory):

    """ Find system events and return them as rest objects  with the user's credentials.
       The factory's rest credentials will be set as the default auth of each of the returned
       system events objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_by_name(self, component_name, rest_client=None, safe=False) -> List[SystemEvent]:
        rest_client = rest_client or self._factory_rest_client
        field_name = SystemEventsFieldsNames.COMPONENT_NAME.value
        system_events = self.get_by_field(field_name=field_name, value=component_name, rest_client=rest_client, safe=safe)
        return system_events

    def get_by_date(self, date, rest_client=None, safe=False) -> SystemEvent:
        rest_client = rest_client or self._factory_rest_client
        field_name = SystemEventsFieldsNames.DATE.value
        system_event = self.get_by_field(field_name=field_name, value=date, rest_client=rest_client, safe=safe)
        assert len(system_event) == 1
        return system_event

    def get_all_dates(self, system_events: List[SystemEvent] = None) -> List[str]:
        system_events = self.get_all() if system_events is None else system_events
        return [s.date for s in system_events]

    def get_the_latest_date(self, component_name) -> SystemEvent:
        system_events_specific_host_names = self.get_by_name(component_name=component_name)
        dates_system_event = self.get_all_dates(system_events=system_events_specific_host_names)
        latest_date = max(dates_system_event, key=lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
        system_event_latest_date = self.get_by_date(date=latest_date)
        return system_event_latest_date

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> List[SystemEvent]:
        """ Find system events by field name<>value and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        system_events = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find system events with field {field_name} = {value} in organization {org_name}")
        system_events_fields = rest_client.system_events.get_system_events()
        for system_event_fields in system_events_fields:
            if system_event_fields[field_name] == value:
                system_event = SystemEvent(rest_client=rest_client, initial_data=system_event_fields)
                system_events.append(system_event)
        if len(system_events):
            logger.debug(f"Found these system events with field {field_name}={value}: \n {system_events}")
            return system_events
        assert safe, f"Didn't find any system events with field {field_name}={value} in organization {self._organization_name}"
        logger.info(f"Didn't find any system events with field {field_name}={value} in organization {self._organization_name}")
        return None

    def get_all(self, rest_client=None, safe=False) -> List[SystemEvent]:
        system_events = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find all system events in organization {org_name}")
        system_events_fields = rest_client.system_events.get_system_events()
        for system_event_fields in system_events_fields:
            system_event = SystemEvent(rest_client=rest_client, initial_data=system_event_fields)
            system_events.append(system_event)
        if len(system_events):
            logger.debug(f"Found these system events: \n {system_events}")
            return system_events
        assert safe, f"Didn't find system events  in organization {self._organization_name}"
        logger.info(f"Didn't find system events in organization {self._organization_name}")
        return system_events


