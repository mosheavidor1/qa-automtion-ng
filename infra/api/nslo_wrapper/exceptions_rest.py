import json
import logging
import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality

logger = logging.getLogger(__name__)


class ExceptionsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Create exception")
    def create_exception(self, params: dict, body: dict):
        url = "/events/create-exception"
        status, response = self._rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=params, body=body)
        if status:
            return True
        else:
            assert False, f"failed to create exception, error: {response}"

    def get_exceptions(self, event_id=None):
        if event_id:
            status, response = self._rest.exceptions.GetEventExceptions(event_id)
        else:
            status, response = self._rest.exceptions.ListExceptions()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        exceptions = json.loads(response.text)
        logger.debug(f"Exceptions are: {exceptions}, event id: {event_id}")
        return exceptions

    @allure.step("Delete exception")
    def delete_exception(self, exception_id, expected_status_code: int = 200):
        status, response = self._rest.exceptions.DeleteException(exception_id)
        err_msg = f"Failed to delete exception, got {response.status_code} instead of {expected_status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=err_msg)
