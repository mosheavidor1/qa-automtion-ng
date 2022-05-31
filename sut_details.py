import os

# set windows 10 64 as default
collector_type = os.getenv("collector_type") if os.getenv("collector_type") is not None else 'WINDOWS_11_64'

# MANAGEMENT DETAILS
management_host = os.getenv("management_host_ip") if os.getenv("management_host_ip") is not None else 'x.x.x.x'
management_ssh_user_name = 'root' #os.getenv("management_ssh_user_name") if os.getenv("management_ssh_user_name") is not None else 'root'
management_ssh_password = 'enSilo$$' # os.getenv("management_ssh_password").replace("17678", "") if os.getenv("management_ssh_password") is not None else 'enSilo$$'
management_ui_admin_user_name = os.getenv("rest_api_user") if os.getenv("rest_api_user") is not None else 'admin'
management_ui_admin_password = os.getenv("rest_api_password") if os.getenv("rest_api_password") is not None else '12345678'
management_registration_password = os.getenv("registration_password") if os.getenv("registration_password") is not None else '12345678'
default_organization = os.getenv("default_organization") if os.getenv("default_organization") is not None else 'Default'

# WINDOWS COLLECTOR CREDENTIALS
win_user_name = 'user1'
win_password = 'P@ssword1!'

debug_mode = True if os.getenv("debug_mode") == 'true' else False
upgrade_management_to_latest_build = True if os.getenv("upgrade_management_to_latest_build") == 'true' else False
upgrade_aggregator_to_latest_build = True if os.getenv("upgrade_aggregator_to_latest_build") == 'true' else False
upgrade_core_to_latest_build = True if os.getenv("upgrade_core_to_latest_build") == 'true' else False
upgrade_collector_latest_build = True if os.getenv("upgrade_collector_to_latest_build") == 'true' else False

# Linux COLLECTOR CREDENTIALS
linux_user_name = 'root'
linux_password = 'enSilo$$'
