from typing import List

import sut_details
from infra.containers.system_component_containers import AggregatorDetails, CoreDetails, CollectorDetails
from infra.enums import OsTypeEnum, CollectorTypes
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

        # TODO - think how to improve it so we don't need to create instance of each collector with OS station
        # connection it can take too much time at the init level
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
            os_type = OsTypeEnum.LINUX
            collector = None
            if 'win' in collector_details.os_family.lower():

                user_name = sut_details.win_user_name
                password = sut_details.win_password

                encrypted_connection = True
                if "windows 7" in collector_details.operating_system.lower():
                    encrypted_connection = False

                collector = WindowsCollector(host_ip=collector_details.ip_address,
                                             user_name=user_name,
                                             password=password,
                                             collector_details=collector_details,
                                             encrypted_connection=encrypted_connection)

                collector.os_station.user_name = user_name
                collector.os_station.password = password
                collector_list.append(collector)

            elif 'linux' in collector_details.os_family.lower():
                collector = LinuxCollector(host_ip=collector_details.ip_address, user_name=sut_details.linux_user_name,
                                           password=sut_details.linux_password, collector_details=collector_details)
                collector_list.append(collector)

            # elif 'osx' in collector_details.os_family.lower():
            #     collector = OsXCollector(host_ip=collector_details.ip_address,
            #                              user_name='root',
            #                              password='enSilo$$',
            #                              collector_details=collector_details)
            #
            # else:
            #     raise Exception(
            #         f"Can not create an collector object since collector from the {collector_details.os_family} family is not known by the automation'")

        return collector_list
