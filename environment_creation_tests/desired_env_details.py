import os

environment_name = os.getenv("environment_name") if os.getenv("environment_name") is not None else None
curr_version = '5.2.0.x'

management_version = os.getenv("management_version") if os.getenv("management_version") is not None else curr_version
aggregator_version = os.getenv("aggregator_version") if os.getenv("aggregator_version") is not None else curr_version
core_version = os.getenv("core_version") if os.getenv("core_version") is not None else curr_version
windows_collector_version = os.getenv("windows_collector_version") if os.getenv("windows_collector_version") is not None else curr_version
linux_collector_version = os.getenv("linux_collector_version") if os.getenv("linux_collector_version") is not None else curr_version

management_and_aggregator_deployment_architecture = os.getenv("management_and_aggregator_deployment_architecture") if os.getenv("management_and_aggregator_deployment_architecture") is not None else 'both'

aggregators_amount = int(os.getenv("aggregators_amount")) if os.getenv("aggregators_amount") is not None else 1
cores_amount = int(os.getenv("cores_amount")) if os.getenv("cores_amount") is not None else 0
windows_11_64_bit = int(os.getenv("windows_11_64_bit")) if os.getenv("windows_11_64_bit") is not None else 0
windows_10_64_bit = int(os.getenv("windows_10_64_bit")) if os.getenv("windows_10_64_bit") is not None else 0
windows_10_32_bit = int(os.getenv("windows_10_32_bit")) if os.getenv("windows_10_32_bit") is not None else 0
windows_8_64_bit = int(os.getenv("windows_8_64_bit")) if os.getenv("windows_8_64_bit") is not None else 0
windows_8_32_bit = int(os.getenv("windows_8_32_bit")) if os.getenv("windows_8_32_bit") is not None else 0
windows_7_64_bit = int(os.getenv("windows_7_64_bit")) if os.getenv("windows_7_64_bit") is not None else 0
windows_7_32_bit = int(os.getenv("windows_7_32_bit")) if os.getenv("windows_7_32_bit") is not None else 0
windows_server_2016 = int(os.getenv("windows_server_2016")) if os.getenv("windows_server_2016") is not None else 0
windows_server_2019 = int(os.getenv("windows_server_2019")) if os.getenv("windows_server_2019") is not None else 0
centOS_6 = int(os.getenv("centOS_6")) if os.getenv("centOS_6") is not None else 0
centOS_7 = int(os.getenv("centOS_7")) if os.getenv("centOS_7") is not None else 0
centOS_8 = int(os.getenv("centOS_8")) if os.getenv("centOS_8") is not None else 0
ubuntu_16 = int(os.getenv("ubuntu_16")) if os.getenv("ubuntu_16") is not None else 0
ubuntu_18 = int(os.getenv("ubuntu_18")) if os.getenv("ubuntu_18") is not None else 0
ubuntu_20 = int(os.getenv("ubuntu_20")) if os.getenv("ubuntu_20") is not None else 0
