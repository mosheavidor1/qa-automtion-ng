import os

vsphere_cluster = int(os.getenv("vsphere_cluster", default=40))

environment_name = os.getenv("environment_name")
curr_version = "5.2.0.x"

management_version = os.getenv("management_version", default=curr_version)
aggregator_version = os.getenv("aggregator_version", default=curr_version)
core_version = os.getenv("core_version", default=curr_version)
windows_collector_version = os.getenv("windows_collector_version", default=curr_version)
linux_collector_version = os.getenv("linux_collector_version", default=curr_version)

management_and_aggregator_deployment_architecture = os.getenv(
    "management_and_aggregator_deployment_architecture", default="both"
)

managements_amount = int(os.getenv("managements_amount", default=1))
components = os.getenv("components", default="true,0,1")  # both?, # of aggrs, # of cores

# External Service Deployment data
aggregators_amount = int(os.getenv("aggregators_amount", default=1))
cores_amount = int(os.getenv("cores_amount", default=1))

windows_11_64_bit = int(os.getenv("windows_11_64_bit", default=0))
windows_10_64_bit = int(os.getenv("windows_10_64_bit", default=0))
windows_10_32_bit = int(os.getenv("windows_10_32_bit", default=0))
windows_8_64_bit = int(os.getenv("windows_8_64_bit", default=0))
windows_8_32_bit = int(os.getenv("windows_8_32_bit", default=0))
windows_7_64_bit = int(os.getenv("windows_7_64_bit", default=0))
windows_7_32_bit = int(os.getenv("windows_7_32_bit", default=0))
windows_server_2016 = int(os.getenv("windows_server_2016", default=0))
windows_server_2019 = int(os.getenv("windows_server_2019", default=0))
centOS_6 = int(os.getenv("centOS_6", default=0))
centOS_7 = int(os.getenv("centOS_7", default=0))
centOS_8 = int(os.getenv("centOS_8", default=0))
ubuntu_16 = int(os.getenv("ubuntu_16", default=0))
ubuntu_18 = int(os.getenv("ubuntu_18", default=0))
ubuntu_20 = int(os.getenv("ubuntu_20", default=0))
