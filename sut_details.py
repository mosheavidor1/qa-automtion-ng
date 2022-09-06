import os

# set windows 10 64 as default
collector_type = os.getenv("collector_type", default='WINDOWS_11_64')

# MANAGEMENT DETAILS
management_host = os.getenv('management_host_ip', default='x.x.x.x')
management_ssh_user_name = 'root'  # os.getenv('management_ssh_user_name', default='root')
management_ssh_password = 'enSilo$$'  # os.getenv('management_ssh_password', default='enSilo$$').replace('17678', '')
rest_api_user = os.getenv('rest_api_user', default='admin')
rest_api_user_password = os.getenv('rest_api_password', default='12345678')
default_organization_name = os.getenv('default_organization', default='Default')
default_organization_registration_password = os.getenv('registration_password', default='12345678')

# WINDOWS COLLECTOR CREDENTIALS
win_user_name = 'user1'
win_password = 'P@ssword1!'

debug_mode = os.getenv('debug_mode') == 'true'
upgrade_management_to_latest_build = os.getenv('upgrade_management_to_latest_build') == 'true'
upgrade_aggregator_to_latest_build = os.getenv('upgrade_aggregator_to_latest_build') == 'true'
upgrade_core_to_latest_build = os.getenv('upgrade_core_to_latest_build') == 'true'
upgrade_collector_latest_build = os.getenv('upgrade_collector_to_latest_build') == 'true'

# Linux COLLECTOR CREDENTIALS
linux_user_name = 'root'
linux_password = 'enSilo$$'

deployment_method = os.getenv('deployment_method', default='external')
