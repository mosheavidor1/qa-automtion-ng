import os


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
