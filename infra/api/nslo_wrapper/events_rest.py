import json
import logging
import allure
from typing import List
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality
logger = logging.getLogger(__name__)


class EventsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Delete events by ids")
    def delete_events(self, event_ids):
        """
        :param event_ids: list of strings or string.
        """
        status, response = self._rest.events.DeleteEvents(event_ids)
        assert status, f'Could not get response from the management. \n{response}'

    def get_events(self, **params) -> List[dict]:
        """ params: Event ID, Device, Collector Group, operatingSystems, deviceIps, fileHash, Process,
        paths, firstSeen, lastSeen, seen, handled, severities, Destinations, Action, rule, strictMode.
        """
        status, response = self._rest.events.ListEvents(**params)
        assert status, f'Could not get response from the management. \n{response}'
        events = json.loads(response.text)
        return events
