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
