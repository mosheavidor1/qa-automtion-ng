import logging
from typing import List

import sut_details
from infra.containers.system_component_containers import AggregatorDetails, CoreDetails
from infra.enums import CollectorTypes
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import CollectorAgent
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.core import Core
from infra.system_components.management import Management
from infra.utils.utils import StringUtils
from infra.api.management_api.organization import is_organization_exist_by_name
from infra.api.api_objects_factory import get_collectors_without_org

logger = logging.getLogger(__name__)


class SystemComponentsFactory:

    @staticmethod
    def get_aggregators(management: Management) -> List[Aggregator]:
        aggr_list = []

        aggregators = management.admin_rest_api_client.system_inventory.get_aggregator_info()
        for single_aggr in aggregators:
            ip_addr, port = StringUtils.get_ip_port_as_tuple(single_aggr.get('ipAddress'))
            aggregator_details = AggregatorDetails(host_name=single_aggr.get('hostName'),
                                                   system_id=single_aggr.get('id'),
                                                   version=single_aggr.get('version'),
                                                   ip_address=ip_addr,
                                                   port=port,
                                                   num_of_agents=single_aggr.get('numOfAgents'),
                                                   num_of_down_agents=single_aggr.get('numOfDownAgents'),
                                                   state=single_aggr.get('state'),
                                                   organization=single_aggr.get('organization'))

            host_ip = management.host_ip if '127.0.0.1' in aggregator_details.ip_address else aggregator_details.ip_address

            new_aggr = Aggregator(host_ip=host_ip,
                                  aggregator_details=aggregator_details)
            aggr_list.append(new_aggr)

        return aggr_list

    @staticmethod
    def get_cores(management: Management) -> List[Core]:
        core_list = []
        cores = management.admin_rest_api_client.system_inventory.get_core_info()
        for single_core in cores:
            ip_addr, port = StringUtils.get_ip_port_as_tuple(single_core.get('ip'))

            core_details = CoreDetails(system_id=single_core.get('id'),
                                       deployment_mode=single_core.get('deploymentMode'),
                                       ip=ip_addr,
                                       port=port,
                                       name=single_core.get('name'),
                                       version=single_core.get('version'),
                                       status=single_core.get('status'),
                                       organization=single_core.get('organization'),
                                       functionality=single_core.get('functionality'))
            core = Core(host_ip=core_details.ip, core_details=core_details)
            core_list.append(core)
        return core_list

    @staticmethod
    def get_collectors_agents(management: Management,
                              collector_type: CollectorTypes) -> List[CollectorAgent]:

        agents_list = []
        collectors_without_org = get_collectors_without_org(safe=True)
        rest_collectors = collectors_without_org if collectors_without_org is not None else []
        if is_organization_exist_by_name(organization_name=management.tenant.organization.get_name()):
            organization_rest_collectors = management.tenant.rest_components.collectors.get_all(safe=True)
            if organization_rest_collectors is not None:
                rest_collectors += organization_rest_collectors

        for rest_collector in rest_collectors:
            if 'windows' in collector_type.value.lower() and 'windows' in rest_collector.get_os_family(from_cache=True).lower():
                user_name = sut_details.win_user_name
                password = sut_details.win_password
                if collector_type.value.lower() not in rest_collector.get_operating_system(from_cache=True).lower():
                    continue
                collector_agent = WindowsCollector(host_ip=rest_collector.get_ip(from_cache=True), user_name=user_name,
                                                   password=password)

                if '64' in collector_type.name and '64' not in collector_agent.os_station.os_architecture:
                    continue

                if '32' in collector_type.name and '32' not in collector_agent.os_station.os_architecture:
                    continue
                agents_list.append(collector_agent)

            elif 'linux' in collector_type.name.lower() and 'linux' in rest_collector.get_os_family(from_cache=True).lower():
                if collector_type.value.lower() not in rest_collector.get_operating_system(from_cache=True).lower():
                    continue

                collector_agent = LinuxCollector(host_ip=rest_collector.get_ip(from_cache=True),
                                                 user_name=sut_details.linux_user_name,
                                                 password=sut_details.linux_password)

                agents_list.append(collector_agent)
        return agents_list
