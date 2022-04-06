import os

# set windows 10 64 as default
collector_type = os.getenv("collector_type") if os.getenv("collector_type") is not None else 'WINDOWS_10_64'

# MANAGEMENT DETAILS
management_host = os.getenv("management_host_ip") if os.getenv("management_host_ip") is not None else None
management_ssh_user_name = 'root'
management_ssh_password = 'enSilo$$'
management_ui_admin_user_name = 'admin'
management_ui_admin_password = '12345678'
management_registration_password = '12345678'

# WINDOWS COLLECTOR CREDENTIALS
win_user_name = 'user1'
win_password = 'P@ssword1!'

debug_mode = True if os.getenv("debug_mode") == 'true' else False

# Linux COLLECTOR CREDENTIALS
linux_user_name = 'root'
linux_password = 'enSilo$$'
