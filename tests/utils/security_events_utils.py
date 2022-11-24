import logging
from infra.system_components.management import Management
from infra.api.management_api.event import EventActionNames

logger = logging.getLogger(__name__)


def validate_event_ui(malware_name, is_blocked: bool, collector_name, management: Management):
    logger.info(f"Validate in ui that event created for malware {malware_name}, is blocked: {is_blocked}")
    tenant = management.tenant
    user = tenant.default_local_admin
    testim_validate_event_params = {
        "eventName": malware_name,
        "collectorName": collector_name,
        "isEventBlock": is_blocked
    }
    logger.info("Wait via api until event created")
    events = user.rest_components.events.get_by_process_name(process_name=malware_name, safe=True,
                                                             wait_for=True)
    assert len(events) == 1, f"ERROR - Created {len(events)} events, expected of 1"
    event = events[0]

    logger.info("Validate event appear in UI")
    management.ui_client.security_events.find_event_and_validate_if_blocked(data=testim_validate_event_params)

    logger.info("Validate event also via api")
    event_process_name = event.get_process_name()
    assert event_process_name == malware_name, f"Event process name is {event_process_name} instead of {malware_name}"
    expected_action = EventActionNames.BLOCK.value if is_blocked else EventActionNames.SIMULATION_BLOCK.value
    assert event.get_action() == expected_action, \
        f"ERROR - event action is '{event.get_action()}' instead of: '{expected_action}'"
