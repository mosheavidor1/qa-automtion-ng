import time
from typing import List

import allure
import pytest

from infra.api.api_object_factory.events_factory import MAX_WAIT_FOR_EVENT
from infra.api.management_api.event import Event
from infra.common_utils import WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
from infra.multi_tenancy.tenant import Tenant
from tests.utils.ip_set_utils import new_ip_set_context
from tests.utils.tenant_utils import new_tenant_context
import logging
from infra.allure_report_handler.reporter import TEST_STEP, Reporter
from infra.enums import CollectorTypes
from infra.system_components.collector import CollectorAgent
from tests.utils.environment_utils import add_collectors_from_pool
logger = logging.getLogger(__name__)


# @allure.epic("Management")
# @allure.feature("IP Sets")
# @pytest.mark.xray('EN-73346')
# def test_create_ip_set_only_with_testim(management):
#     """
#     This test run Testim.io
#     """
#     malware_name = "DynamicCodeTests.exe"
#     test_im_params = {"eventName": malware_name}
#     management.ui_client.ip_set.set_new_ip_set(data=test_im_params)


@allure.epic("Management")
@allure.feature("IP Sets")
@pytest.mark.management_sanity
@pytest.mark.management_full_regression
@pytest.mark.full_regression
@pytest.mark.ipset
@pytest.mark.sanity
@pytest.mark.ip_set_sanity
@pytest.mark.xray('EN-76261')
def test_ip_sets_events_sanity(fx_system_without_events_and_exceptions, aggregator, collector):

    """
     Test that event should not be in the Event Viewer after creating exception with ip set included the destinattion event

        1. create new organization
        2. Connect a collector to the new organization
        3. Set to Prevention all policies for the default organization and for the new organization.
        4. send event "StackPivotTests.exe" from both collector verify that the event is generated in both organizations
        5. extract destination ip of the "stackPivot.ext" event
        6. define new ip set with the destination ip.
        7. create an exception from the event from the collector of new organization and set as destination the IP set.
        8. Send the same event from the collector of new organization verify that the event is not generated
        9. Send the same event from the collector of default organization verify that the event is generated in the default organization
        10. Send another event from the collector of new organization verify that the event is generated in the new organization
        11. update ip set- "Included IPs" - delete the previous destination IP and set 1.1.1.1.
            "Excluded IPs" - add the previous destination IP
        12. Send the same event from the collector from new organization verify the event is generated in the new organization

    """

    management = fx_system_without_events_and_exceptions
    original_tenant = management.tenant
    original_tenant_organization_name = original_tenant.organization.get_name(from_cache=True)
    original_collector_agent = collector
    original_rest_collector = original_tenant.rest_components.collectors.get_by_ip(ip=original_collector_agent.host_ip)
    malware_name = "StackPivotTests.exe"
    another_malware = "DynamicCodeTests.exe"

    with new_tenant_context(management=management) as additional_tenant:
        additional_tenant_obj = additional_tenant[0]
        additional_tenant_org_name = additional_tenant_obj.organization.get_name(from_cache=True)
        additional_collector_obj_in_new_tenant: CollectorAgent = None

        desired_version = original_rest_collector.get_version()
        desired_collectors = {
            CollectorTypes.WINDOWS_10_64: 1
        }

        with add_collectors_from_pool(tenant=additional_tenant_obj,
                                      desired_version=desired_version,
                                      aggregator_ip=aggregator.host_ip,
                                      organization=additional_tenant_org_name,
                                      registration_password=additional_tenant_obj.organization.registration_password,
                                      desired_collectors_dict=desired_collectors) as dynamic_collectors:

            additional_collector_obj_in_new_tenant = dynamic_collectors[0]
            additional_collector_rest_object = additional_tenant_obj.rest_components.collectors.get_by_ip(
                ip=additional_collector_obj_in_new_tenant.host_ip)

            original_tenant.turn_on_prevention_mode()
            additional_tenant_obj.turn_on_prevention_mode()

            events_in_original_org = generate_event_from_specific_collector_in_specific_organization_with_validation(
                tenant=original_tenant,
                collector_agent=original_collector_agent,
                num_of_expected_events=1,
                malware_name=malware_name)

            events_in_additional_org = generate_event_from_specific_collector_in_specific_organization_with_validation(
                tenant=additional_tenant_obj,
                collector_agent=additional_collector_obj_in_new_tenant,
                num_of_expected_events=1,
                malware_name=malware_name)

            # assert False, "add collectors from pool context"

            with TEST_STEP(f"STEP- extract destination ip of the {malware_name} event - organization {original_tenant_organization_name}"):
                destination_event_ip = events_in_original_org[0].get_destination_ip()
                Reporter.report(message=f"Destination IP of the event: {destination_event_ip}", logger_func=logger.info)

            with new_ip_set_context(tenant=additional_tenant_obj,
                                    destination_event=destination_event_ip,) as ip_set:

                with TEST_STEP(f"STEP- create an exception for the event from the collector that found in "
                               f"the additional organization: {additional_tenant_org_name} and set the "
                               f"destination IP {destination_event_ip} as IP set for this exception"):

                    event_id = events_in_additional_org[0].id
                    additional_tenant_obj.default_local_admin.rest_components.exceptions.create_exception_for_event(
                        event_id=event_id,
                        groups=[additional_collector_rest_object.get_group_name()],
                        destinations=[ip_set.name])

                    # TODO - Implement smarter logic in order to wait till config will drill down to collector
                    time.sleep(WAIT_FOR_COLLECTOR_NEW_CONFIGURATION)

                with TEST_STEP(f"STEP - Delete all event in the "
                               f"additional organization {additional_tenant_org_name}"):
                    additional_tenant_obj.default_local_admin.rest_components.events.delete_all(safe=True, wait_sec=1)
                    original_tenant.default_local_admin.rest_components.events.delete_all(safe=True)

                with TEST_STEP(f"STEP- send the same event from the collector in "
                               f"the additional organization and verify that the event is not "
                               f"generated within timeout of {MAX_WAIT_FOR_EVENT} seconds "):
                    generate_event_from_specific_collector_in_specific_organization_with_validation(
                        tenant=additional_tenant_obj,
                        collector_agent=additional_collector_obj_in_new_tenant,
                        malware_name=malware_name,
                        num_of_expected_events=0,
                        wait_for_event_timeout=MAX_WAIT_FOR_EVENT)

                with TEST_STEP(f"STEP - send the same event from the collector in "
                               f"the default organization and verify that the event is generated"):
                    generate_event_from_specific_collector_in_specific_organization_with_validation(
                        tenant=original_tenant,
                        collector_agent=original_collector_agent,
                        malware_name=malware_name,
                        num_of_expected_events=1)

                with TEST_STEP(f"STEP- send another event {another_malware} from the collector in "
                               f"the additional organization {additional_tenant_org_name} that is "
                               f"not related to the exception and the IP set "
                               f"and verify that the event is generated"):
                    generate_event_from_specific_collector_in_specific_organization_with_validation(
                        tenant=additional_tenant_obj,
                        collector_agent=additional_collector_obj_in_new_tenant,
                        malware_name=another_malware,
                        num_of_expected_events=1)

                with TEST_STEP(f"STEP - update ip set- Included IPs - set 1.1.1.1 "
                               f"Excluded IPs - add the destination IP { destination_event_ip}"):
                    # TODO - change here to ip_set.update()... instead of the code below
                    ip_set.update_fields(include=['1.1.1.1'], exclude=destination_event_ip)

                    # TODO - Implement smarter logic in order to wait till config will drill down to collector
                    time.sleep(WAIT_FOR_COLLECTOR_NEW_CONFIGURATION)

                with TEST_STEP(f"STEP- generate another event {malware_name} from the collector that found "
                               f"in {additional_tenant_org_name} organization "
                               f"and verify the event is generated after updating the IP set - "
                               f"expecting to see the event"):

                    generate_event_from_specific_collector_in_specific_organization_with_validation(
                        tenant=additional_tenant_obj,
                        collector_agent=additional_collector_obj_in_new_tenant,
                        malware_name=malware_name,
                        num_of_expected_events=1)

                    # expecting 2 events - StackPivotTests.exe & DynamicCodeTests.exe
                    all_events = additional_tenant_obj.default_local_admin.rest_components.events.get_all()
                    assert len(all_events) == 2, "Expected 2 events, 1 of the updated expcetion, " \
                                                 "and 1 that was already exist from the previous step " \
                                                 "(StackPivotTests.exe and DynamicCodeTests.exe)"


def generate_event_from_specific_collector_in_specific_organization_with_validation(tenant: Tenant,
                                                                                    collector_agent: CollectorAgent,
                                                                                    malware_name: str,
                                                                                    num_of_expected_events: int,
                                                                                    wait_for_event_timeout: int = 61) -> List[Event]:
    with TEST_STEP(
            f"STEP- generate {malware_name} event the collector that found in "
            f"organization {tenant.organization.get_name(from_cache=True)} and "
            f"wait for {num_of_expected_events} of expceted events"):
        safe = num_of_expected_events == 0
        collector_agent.create_event(malware_name=malware_name)
        events_in_org = tenant.default_local_admin.rest_components.events.get_by_process_name(process_name=malware_name,
                                                                                              safe=safe,
                                                                                              wait_for=True,
                                                                                              timeout=wait_for_event_timeout)
        if events_in_org is None:
            events_in_org = []

        Reporter.report(f"There are {len(events_in_org)} events of {malware_name} in the current organization")

        assert len(events_in_org) == num_of_expected_events, f"ERROR - Created {len(events_in_org)} events, expected for {num_of_expected_events} exactly"
        return events_in_org
