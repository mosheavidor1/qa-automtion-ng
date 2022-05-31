from ensilo.platform.rest.nslo_management_rest import NsloManagementConnection, NsloRest
from infra.api.nslo_wrapper.administrator_rest import AdministratorRest
from infra.api.nslo_wrapper.communication_control_rest import CommunicationControlRest
from infra.api.nslo_wrapper.events_rest import EventsRest
from infra.api.nslo_wrapper.exceptions_rest import ExceptionsRest
from infra.api.nslo_wrapper.exclusions_rest import ExclusionsRest
from infra.api.nslo_wrapper.forensics_rest import ForensicsRest
from infra.api.nslo_wrapper.hash_rest import HashRest
from infra.api.nslo_wrapper.integrations_rest import IntegrationRest
from infra.api.nslo_wrapper.iot_rest import IoTRest
from infra.api.nslo_wrapper.ip_sets_rest import IpSetsRest
from infra.api.nslo_wrapper.organizations_rest import OrganizationsRest
from infra.api.nslo_wrapper.playbooks_rest import PlaybooksRest
from infra.api.nslo_wrapper.policies_rest import PoliciesRest
from infra.api.nslo_wrapper.system_events_rest import SystemEventsRest
from infra.api.nslo_wrapper.system_inventory_rest import SystemInventoryRest
from infra.api.nslo_wrapper.threat_hunting_rest import ThreatHuntingRest
from infra.api.nslo_wrapper.threat_hunting_settings_rest import ThreatHuntingSettingsRest
from infra.api.nslo_wrapper.users_rest import UsersRest


class RestCommands(object):
    """
    Class with different rest API methods.
    """

    def __init__(self, management_ip, management_user, management_password, organization=None):
        self.management_ip = management_ip
        self.management_user = management_user
        self.management_password = management_password
        self.rest = NsloRest(NsloManagementConnection(management_ip, management_user, management_password,
                                                      organization=organization))
        self.administrator = AdministratorRest(nslo_rest=self.rest)
        self.communication_control = CommunicationControlRest(nslo_rest=self.rest)
        self.events = EventsRest(nslo_rest=self.rest)
        self.exceptions = ExceptionsRest(nslo_rest=self.rest)
        self.exclusions = ExclusionsRest(nslo_rest=self.rest)
        self.forensics = ForensicsRest(nslo_rest=self.rest)
        self.hash = HashRest(nslo_rest=self.rest)
        self.integration = IntegrationRest(nslo_rest=self.rest)
        self.iot = IoTRest(nslo_rest=self.rest)
        self.ip_sets = IpSetsRest(nslo_rest=self.rest)
        self.organizations = OrganizationsRest(nslo_rest=self.rest)
        self.playbooks = PlaybooksRest(nslo_rest=self.rest)
        self.policies = PoliciesRest(nslo_rest=self.rest)
        self.system_events = SystemEventsRest(nslo_rest=self.rest)
        self.system_inventory = SystemInventoryRest(nslo_rest=self.rest)
        self.threat_hunting = ThreatHuntingRest(nslo_rest=self.rest)
        self.threat_hunting_settings = ThreatHuntingSettingsRest(nslo_rest=self.rest)
        self.users_rest = UsersRest(nslo_rest=self.rest)
