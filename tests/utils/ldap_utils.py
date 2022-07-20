def get_base_ad_server_ldap_configuration():
    ad_server_configuration = {"security_level": "None",
                               "LDAP_host": "10.51.122.21",
                               "Directory_type": "ActiveDirectory",
                               "Bind_User_DN": "CN=domainAccount,CN=Users,DC=automation,DC=com",
                               "Bind_Password": "12345678",
                               "BaseDN": "DC=automation,DC=com",
                               "UserGroupName": "CN=testUserGroup,OU=Groups,OU=QA,DC=automation,DC=com",
                               "LocalAdminGroupName": "CN=testAdminGroup,OU=Groups,OU=QA,DC=automation,DC=com",
                               "AdminGroupName": "CN=testhostergroup,OU=Groups,OU=QA,DC=automation,DC=com"
                               }

    return ad_server_configuration


def get_login_details_of_ad_ldap_non_admin_user():
    openldap_user = {
                    "loginUser": "TestUser",
                    "loginPassword": "12345678"
                    }

    return openldap_user


def get_login_details_of_ad_ldap_local_admin():
    openldap_user = {
        "loginUser": "TestAdmin",
        "loginPassword": "12345678"
    }

    return openldap_user


def get_base_openldap_configuration():
    openldap_server_configuration = {"security_level": "None",
                                     "LDAP_host": "10.51.122.19",
                                     "Directory_type": "OpenLDAP",
                                     "Bind_User_DN": "CN=admin,DC=openldap,DC=com",
                                     "Bind_Password": "enSilo$$",
                                     "BaseDN": " DC=openldap,DC=com",
                                     "UserGroupName": "cn=test3.1.1,ou=Groups,dc=openldap,dc=com",
                                     "LocalAdminGroupName": "",
                                     "AdminGroupName": ""
                                     }

    return openldap_server_configuration
