import json
from typing import List
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality


class SystemEventsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    def get_system_events(self, expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.systemEvents.ListSystemEvents()
        assert status, f'Could not get response from the management. \n{response}'
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List system events - expected response code: {expected_status_code}, actual: {response.status_code}")

        system_events = json.loads(response.content)
        return system_events

