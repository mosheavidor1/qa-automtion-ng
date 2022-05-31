import json
import time

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality


class EventsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)
        
    @allure.step("Get security events")
    def get_security_events(self,
                            validation_data,
                            timeout=60,
                            sleep_delay=2,
                            fail_on_no_events=True):
        """
        :param validation_data: dictionary of the data to get.
                                options of parameters: Event ID, Device, Collector Group, operatingSystems, deviceIps,
                                fileHash, Process, paths, firstSeen, lastSeen, seen, handled, severities, Destinations,
                                Action, rule, strictMode.

        :return: list of dictionaries with the event info.
                 if the request failed or there were no events found -> False
        """

        start_time = time.time()
        is_found = False
        error_message = None
        events = []
        while time.time() - start_time < timeout and not is_found:
            try:
                Reporter.report("Trying again to get events")
                status, response = self._rest.events.ListEvents(**validation_data)
                if not status:
                    error_message = f'Could not get response from the management. \n{response}'

                events = json.loads(response.text)
                Reporter.report(f"Got these events: {events}")
                if not len(events):
                    error_message = 'No event with the given parameters found.'
                    time.sleep(sleep_delay)
                else:
                    is_found = True
                    Reporter.report(f'Successfully got information of {len(events)} events.')

            except Exception as e:
                Reporter.report(f'{error_message}, trying again')
                time.sleep(sleep_delay)

        if not is_found and fail_on_no_events:
            assert False, f"{error_message} after waiting {timeout} seconds"

        return events

    def delete_event_by_name(self, eventName):
        urlget = "/events/list-events"
        response = self._rest.passthrough.ExecuteRequest(urlget, mode='get', inputParams=None)[1].text
        eventsList = json.loads(response)
        eventsIds = []
        for item in eventsList:
            try:
                name = item["process"]
                if eventName in str(name):
                    eventsIds.append(item["eventId"])
            except:
                pass
        if len(eventsIds):
            return self.delete_events(eventsIds)
        else:
            Reporter.report('There is no events to delete with the given name.')
            return False

    def delete_events(self, event_ids):
        """
        :param event_ids: list of strings or string.
        """
        status, response = self._rest.events.DeleteEvents(event_ids)
        event_info = self.get_security_events({'Event ID': event_ids})
        if not status:
            assert False, f'Could not get response from the management. \n{response}'

        if event_info:
            assert False, 'Could not delete the given events.'

        Reporter.report('Deleted the given events successfully.')
        return True

    @allure.step("Delete all events")
    def delete_all_events(self, timeout=60):
        event_ids = []
        response = self._rest.events.ListEvents()
        as_list_of_dicts = json.loads(response[1].text)
        for single_event in as_list_of_dicts:
            event_id = single_event.get('eventId')
            event_ids.append(event_id)
            Reporter.report(f"Going to sleep {timeout} seconds becuase this is the period of time that took for "
                            f"deletion in the backend - non configurable conifguration")

        if len(event_ids) > 0:
            self._rest.events.DeleteEvents(eventIds=event_ids)

        else:
            Reporter.report("No events, nothing to delete")
            Reporter.report(f"Going to sleep {timeout} becuase the previous test could delete the events and we got to"
                            f" this step within the {timeout} sec of deletion period, therefore we can not assume it "
                            f"removed in the backend")

        time.sleep(timeout)