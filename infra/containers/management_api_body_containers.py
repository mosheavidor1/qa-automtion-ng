from typing import List

from infra.enums import UserRoles


class OrganizationRestData:

    def __init__(self,
                 expiration_date: str,
                 organization_name: str,
                 forensics_and_EDR: bool,
                 vulnerability_and_IoT: bool,
                 servers_allocated: int,
                 workstations_allocated: int,
                 iot_allocated: int):
        self.expirationDate = expiration_date
        self.name = organization_name
        self.forensicsAndEDR = forensics_and_EDR
        self.vulnerabilityAndIoT = vulnerability_and_IoT
        self.workstationsAllocated = str(workstations_allocated)
        self.serversAllocated = str(servers_allocated)
        self.iotAllocated = str(iot_allocated)


class CreateOrganizationRestData(OrganizationRestData):

    def __init__(self,
                 expiration_date: str,
                 organization_name: str,
                 password: str,
                 password_confirmation: str,
                 forensics_and_EDR: bool,
                 vulnerability_and_IoT: bool,
                 servers_allocated: int,
                 workstations_allocated: int,
                 iot_allocated: int):
        """

        :param expiration_date: should be in the format  yyyy-MM-dd. for example 2023-01-28
        :param organization_name:
        :param password:
        :param password_confirmation:
        :param forensics_and_EDR:
        :param vulnerability_and_IoT:
        :param servers_allocated:
        :param workstations_allocated:
        :param iot_allocated:
        """

        super().__init__(expiration_date=expiration_date,
                         organization_name=organization_name,
                         servers_allocated=servers_allocated,
                         workstations_allocated=workstations_allocated,
                         iot_allocated=iot_allocated,
                         forensics_and_EDR=forensics_and_EDR,
                         vulnerability_and_IoT=vulnerability_and_IoT)

        self.password = password
        self.passwordConfirmation = password_confirmation


class UserRestData:
    def __init__(self,
                 organization: str,
                 email: str,
                 first_name: str,
                 last_name: str,
                 roles: List[UserRoles],
                 title: str,
                 user_name: str):
        self.organization = organization
        self.email = email
        self.firstName = first_name
        self.lastName = last_name
        self.roles = roles
        self.title = title
        self.username = user_name


class CreateUserRestData(UserRestData):
    def __init__(self,
                 organization: str,
                 email: str,
                 first_name: str,
                 last_name: str,
                 roles: List[UserRoles],
                 title: str,
                 user_name: str,
                 password: str,
                 confirm_password: str):
        super().__init__(organization=organization,
                         email=email,
                         first_name=first_name,
                         last_name=last_name,
                         roles=roles,
                         title=title,
                         user_name=user_name)
        self.password = password
        self.confirmPassword = confirm_password



