from typing import List

import sut_details
from infra.containers.system_component_containers import AggregatorDetails, CoreDetails, CollectorDetails
from infra.enums import CollectorTypes
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import Collector
from infra.system_components.collectors.linux_os.linux_collector import LinuxCollector
from infra.system_components.collectors.windows_os.windows_collector import WindowsCollector
from infra.system_components.core import Core
from infra.system_components.management import Management
from infra.utils.utils import StringUtils


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
    def get_collectors(management: Management,
                       collector_type: CollectorTypes) -> List[Collector]:

        collector_list = []
        collectors = management.admin_rest_api_client.system_inventory.get_collector_info()

        if management.admin_rest_api_client.organizations.is_organization_exist(management.tenant.organization):
            collectors += management.admin_rest_api_client.system_inventory.get_collector_info(organization=management.tenant.organization)

        for single_collector in collectors:
            collector_details = CollectorDetails(system_id=single_collector.get('id'),
                                                 name=single_collector.get('name'),
                                                 collector_group_name=single_collector.get('collectorGroupName'),
                                                 operating_system=single_collector.get('operatingSystem'),
                                                 ip_address=single_collector.get('ipAddress'),
                                                 last_seen_time=single_collector.get('lastSeenTime'),
                                                 mac_addresses=single_collector.get('macAddresses'),
                                                 account_name=single_collector.get('accountName'),
                                                 organization=single_collector.get('organization'),
                                                 state=single_collector.get('state'),
                                                 os_family=single_collector.get('osFamily'),
                                                 state_additional_info=single_collector.get('stateAdditionalInfo'),
                                                 version=single_collector.get('version'),
                                                 logged_users=single_collector.get('loggedUsers'),
                                                 system_information=single_collector.get('systemInformation'))

            if 'windows' in collector_type.name.lower() and 'windows' in collector_details.os_family.lower():

                user_name = sut_details.win_user_name
                password = sut_details.win_password
                encrypted_connection = True

                match collector_type:

                    case collector_type.WINDOWS_11_64:
                        if 'windows 11' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.WINDOWS_10_64 | collector_type.WINDOWS_10_32:
                        if 'windows 10' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.WINDOWS_8_64:
                        # TODO - no logic yet - skipping create collector instance
                        continue

                    case collector_type.WINDOWS_7_64 | collector_type.WINDOWS_7_32:
                        encrypted_connection = False
                        if 'windows 7' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.WIN_SERVER_2019 | collector_type.WIN_SERVER_2016:
                        # TODO - no logic yet - skipping create collector instance
                        continue

                collector = WindowsCollector(host_ip=collector_details.ip_address,
                                             user_name=user_name,
                                             password=password,
                                             collector_details=collector_details,
                                             encrypted_connection=encrypted_connection)

                if '64' in collector_type.name and '64' not in collector.os_station.os_architecture:
                    continue

                if '32' in collector_type.name and '32' not in collector.os_station.os_architecture:
                    continue

                collector_list.append(collector)

            elif 'linux' in collector_type.name.lower() and 'linux' in collector_details.os_family.lower():

                match collector_type:

                    case collector_type.LINUX_CENTOS_8:
                        if 'centos 8' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.LINUX_CENTOS_7:
                        if 'centos 7' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.LINUX_CENTOS_6:
                        if 'centos 7' not in collector_details.operating_system.lower():
                            continue

                    case collector_type.LINUX_UBUNTU_20:
                        # TODO - no logic yet - skipping create collector instance
                        continue
                    case collector_type.LINUX_UBUNTU_18:
                        # TODO - no logic yet - skipping create collector instance
                        continue
                    case collector_type.LINUX_UBUNTU_16:
                        # TODO - no logic yet - skipping create collector instance
                        continue

                collector = LinuxCollector(host_ip=collector_details.ip_address, user_name=sut_details.linux_user_name,
                                           password=sut_details.linux_password, collector_details=collector_details)

                collector_list.append(collector)

        return collector_list
