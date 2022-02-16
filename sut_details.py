import os


# MANAGEMENT DETAILS
management_host = '10.151.120.187'
management_ssh_user_name = 'root'
management_ssh_password = 'enSilo$$'
management_ui_admin_user_name = 'admin'
management_ui_admin_password = '12345678'
management_registration_password = '12345678'

# WINDOWS COLLECTOR CREDENTIALS
win_user_name = 'user1'
win_password = 'P@ssword1!'

developer_mode = True if os.getenv("developer_mode") == 'true' else False
