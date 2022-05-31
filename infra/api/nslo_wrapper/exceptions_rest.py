import json
import time

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality


class ExceptionsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)
        
    def create_exception(self, eventId, groups=None, destinations=None, organization="Default", useAnyPath=None,
                         useInException=None, wildcardFiles=None, wildcardPaths=None, **kwargs):
        """
          create exception
          :param eventId: event id for create exception
          :param groups: list of string or None for all groups
          :param destinations: list of destinations or None for all destinations
          :param organization: string or none for all organizations
          :param useAnyPath: useAnyPath
          :param useInException: useInException
          :param wildcardFiles: wildcardFiles
          :param wildcardPaths: wildcardPaths
          :return: True or False.
          """

        url = "/events/create-exception"
        kwargs["eventId"] = eventId
        if groups:
            kwargs["collectorGroups"] = groups
            kwargs["allCollectorGroups"] = False
        else:
            kwargs["allCollectorGroups"] = True
        if destinations:
            kwargs["destinations"] = destinations
            kwargs["allDestinations"] = False
        else:
            kwargs["allDestinations"] = True
        if organization:
            kwargs["organization"] = organization
            kwargs["allOrganizations"] = False
        else:
            kwargs["allOrganizations"] = True

        body = {}
        if useAnyPath:
            body["useAnyPath"] = useAnyPath
        if useInException:
            body["useInException"] = useInException
        if wildcardFiles:
            body["wildcardFiles"] = wildcardFiles
        if wildcardPaths:
            body["wildcardPaths"] = wildcardPaths

        status, response = self._rest.passthrough.ExecuteRequest(url=url, mode="post", inputParams=kwargs, body=body)
        if status:
            return True
        else:
            assert False, f"failed to create exception, error: {response}"

    @allure.step("Get exceptions")
    def get_exceptions(self, event_id=None):
        """
        :param event_id: string, optional, if no event id given returns all the exceptions
        :return: list of dictionaries with the following parameters:
                    exceptionId, originEventId, userName, updatedAt, createdAt, comment, selectedDestinations,
                    optionalDestinations, selectedCollectorGroups, optionalCollectorGroups, alerts.
        """
        if event_id:
            status, response = self._rest.exceptions.GetEventExceptions(event_id)
        else:
            status, response = self._rest.exceptions.ListExceptions()

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        exceptions = json.loads(response.text)

        Reporter.report(f'Successfully got information of the following event id: {event_id}. '
                        f'Exceptions are: {exceptions}')
        return exceptions

    def delete_exception(self, exception_id):
        """
        :param exceptionId: string.
        """
        status, response = self._rest.exceptions.DeleteException(exception_id)

        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        Reporter.report(f'Deleted the exception of the event: {exception_id} successfully.')
        return True

    @allure.step("Delete all exceptions")
    def delete_all_exceptions(self, timeout=60):
        exception_ids = []
        response = self._rest.exceptions.ListExceptions()
        as_list_of_dicts = json.loads(response[1].text)
        for single_exception in as_list_of_dicts:
            event_id = single_exception.get('exceptionId')
            exception_ids.append(event_id)

        if len(exception_ids) > 0:
            for exc_id in exception_ids:
                self._rest.exceptions.DeleteException(exceptionId=exc_id)
            time.sleep(timeout)
        else:
            Reporter.report("No execptions, nothing to delete")