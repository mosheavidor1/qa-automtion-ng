class ManagementDetails:

    def __init__(self,
                 license_expiration_date: str,
                 management_version: str,
                 management_hostname: str,
                 management_external_ip: str,
                 management_internal_ip: str):
        self.license_expiration_date = license_expiration_date
        self.management_version = management_version
        self.management_hostname = management_hostname
        self.management_external_ip = management_external_ip
        self.management_internal_ip = management_internal_ip


class AggregatorDetails:

    def __init__(self,
                 system_id: int,
                 host_name: str,
                 version: str,
                 ip_address: str,
                 port: str,
                 num_of_agents: str,
                 num_of_down_agents: str,
                 state: str,
                 organization: str):
        self.host_name = host_name
        self.system_id = system_id
        self.version = version
        self.ip_address = ip_address
        self.port = port
        self.num_of_agents = num_of_agents
        self.num_of_down_agents = num_of_down_agents
        self.state = state
        self.organization = organization


class CoreDetails:
    def __init__(self,
                 system_id: int,
                 deployment_mode: str,
                 ip: str,
                 port: str,
                 name: str,
                 version: str,
                 status: str,
                 organization: str,
                 functionality: str):
        self.system_id = system_id
        self.deployment_mode = deployment_mode
        self.ip = ip
        self.port = port
        self.name = name,
        self.version = version
        self.status = status
        self.organization = organization
        self.functionality = functionality


class CollectorDetails:

    def __init__(self,
                 system_id: int,
                 name: str,
                 collector_group_name: str,
                 operating_system: str,
                 ip_address: str,
                 last_seen_time: str,
                 mac_addresses: [str],
                 account_name: str,
                 organization: str,
                 state: str,
                 os_family: str,
                 state_additional_info: str,
                 version: str,
                 logged_users: [str],
                 system_information: dict):

        self.system_id = system_id
        self.name = name
        self.collector_group_name = collector_group_name
        self.operating_system = operating_system
        self.ip_address = ip_address
        self.last_seen_time = last_seen_time
        self.mac_addresses = mac_addresses
        self.account_name = account_name
        self.organization = organization
        self.state = state
        self.os_family = os_family
        self.state_additional_info = state_additional_info
        self.version = version
        self.logged_users = logged_users
        self.system_information = system_information
