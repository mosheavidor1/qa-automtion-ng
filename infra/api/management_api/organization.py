import allure
import logging
from typing import List
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api import ADMIN_REST
import sut_details
from infra.utils.utils import StringUtils

logger = logging.getLogger(__name__)

DEFAULT_LICENSE_CAPACITY = 100
DEFAULT_ORGANIZATION_NAME = sut_details.default_organization_name  # Gabi why we need to get it from sut details ? is it not constent 'Default' ?
MANAGEMENT_REGISTRATION_PASSWORD = sut_details.default_organization_registration_password


class OrgFieldsNames(Enum):
    ID = 'organizationId'
    EXPIRATION_DATE = 'expirationDate'
    ORG_NAME = 'name'
    FORENSICS_AND_EDR = 'forensicsAndEDR'
    FORENSICS = 'forensics'
    EDR = 'edr'
    VULNERABILITY = 'vulnerabilityAndIoT'
    REGISTRATION_PASSWORD = 'password'
    PASSWORD_CONFIRMATION = 'passwordConfirmation'
    SERVERS_LICENCES = 'serversAllocated'
    WORK_STATION_LICENCES = 'workstationsAllocated'
    IOT_LICENCES = 'iotAllocated'
    WORK_STATIONS_IN_USE = 'workstationsInUse'


class Organization(BaseApiObj):
    """ A wrapper of our internal rest client for working with organization capabilities.
    Some actions like 'create' requires only admin credentials and some actions like update can be performed
    with user's credentials """

    def __init__(self, rest_client: RestCommands, password: str, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._registration_password = password
        self._id = initial_data[OrgFieldsNames.ID.value]  # Static, unique identifier

    @property
    def id(self) -> int:
        return self._id

    @property
    def registration_password(self) -> str:
        """ Need to maintain password because nslo post/get organizations api response doesn't contain the password """
        return self._registration_password

    @classmethod
    @allure.step("Create organization")
    def create(cls, rest_client: RestCommands, name, password, expected_status_code=200, **optional_data):
        """ Create new organization in management and return its api wrapper """
        assert not is_organization_exist_by_name(organization_name=name), f"Organization {name} already exist in MGMT"
        logger.info(f"Create new Organization '{name}'")
        expiration_date = optional_data.get(OrgFieldsNames.EXPIRATION_DATE.value, get_default_org_expiration_date())
        organization_data = {
            OrgFieldsNames.ORG_NAME.value: name,
            OrgFieldsNames.EXPIRATION_DATE.value: expiration_date,
            OrgFieldsNames.FORENSICS_AND_EDR.value: True,
            OrgFieldsNames.VULNERABILITY.value: True,
            OrgFieldsNames.REGISTRATION_PASSWORD.value: password,
            OrgFieldsNames.PASSWORD_CONFIRMATION.value: password,
            OrgFieldsNames.SERVERS_LICENCES.value: optional_data.get(OrgFieldsNames.SERVERS_LICENCES.value,
                                                                     DEFAULT_LICENSE_CAPACITY),
            OrgFieldsNames.WORK_STATION_LICENCES.value: optional_data.get(OrgFieldsNames.WORK_STATION_LICENCES.value,
                                                                          DEFAULT_LICENSE_CAPACITY),
            OrgFieldsNames.IOT_LICENCES.value: optional_data.get(OrgFieldsNames.IOT_LICENCES.value,
                                                                 DEFAULT_LICENSE_CAPACITY)
        }
        organization_data[OrgFieldsNames.FORENSICS.value] = organization_data[OrgFieldsNames.FORENSICS_AND_EDR.value]
        organization_data[OrgFieldsNames.EDR.value] = organization_data[OrgFieldsNames.FORENSICS_AND_EDR.value]
        ADMIN_REST().organizations.create_organization(org_data=organization_data,
                                                       expected_status_code=expected_status_code)
        new_org_data = get_organization_fields_by_name(organization_name=name, safe=False)
        if expected_status_code == 200:
            _compare_new_org_data(expected_data=organization_data, actual_data=new_org_data)
        organization = cls(rest_client=rest_client, password=password, initial_data=new_org_data)
        return organization

    def get_expiration_date(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.EXPIRATION_DATE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        value = StringUtils.get_txt_by_regex(text=value, regex=r'(\d+-\d+-\d+)', group=1)
        return value

    def get_name(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.ORG_NAME.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_servers_licences_capacity(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.SERVERS_LICENCES.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_works_station_licences_capacity(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.WORK_STATION_LICENCES.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_works_station_licences_in_use(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.WORK_STATIONS_IN_USE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_iot_licences_capacity(self, from_cache=None, update_cache=True):
        field_name = OrgFieldsNames.IOT_LICENCES.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    @allure.step("Update organization license capacity")
    def update_license_capacity(self, new_license_capacity, expected_status_code=200):
        logger.info(f"Update {self} license capacity to {new_license_capacity}")
        new_fields = [(OrgFieldsNames.SERVERS_LICENCES.value, new_license_capacity),
                      (OrgFieldsNames.WORK_STATION_LICENCES.value, new_license_capacity),
                      (OrgFieldsNames.IOT_LICENCES.value, new_license_capacity)]
        self.update_fields(new_fields=new_fields, expected_status_code=expected_status_code)

    @allure.step("Delete organization")
    def _delete(self, expected_status_code=200):
        """ Organization that is actually a tenant can be deleted via management only """
        logger.info(f"Delete {self}")
        ADMIN_REST().organizations.delete_organization(organization_name=self.get_name(),
                                                       expected_status_code=expected_status_code)
        self._validate_deletion()

    def _get_field(self, field_name, from_cache, update_cache):
        from_cache = from_cache if from_cache is not None else self._use_cache
        if from_cache:
            value = self._cache[field_name]
        else:
            updated_value = self.get_fields()[field_name]
            value = updated_value
            if update_cache:
                self._cache[field_name] = updated_value
        return value

    def get_fields(self, safe=False, update_cache_data=False, rest_client=ADMIN_REST()) -> dict:
        """ Get organization fields by its id """
        orgs_fields = ADMIN_REST().organizations.get_all_organizations()
        for org_fields in orgs_fields:
            if org_fields[OrgFieldsNames.ID.value] == self.id:
                logger.debug(f"{self} updated data from management: \n {org_fields}")
                if update_cache_data:
                    self.cache = org_fields
                return org_fields
        assert safe, f"Organization with id {self.id} was not found"
        logger.debug(f"Organization with id {self.id} was not found")
        return None

    def update_fields(self, new_fields: List[tuple], expected_status_code=200):
        # check if local admin user can update all these fields if not add rest client as argument
        current_name = self.get_name(from_cache=False)
        self.update_all_cache()
        updated_data = {
            OrgFieldsNames.EXPIRATION_DATE.value: self.get_expiration_date(from_cache=True),
            OrgFieldsNames.ORG_NAME.value: self.get_name(from_cache=True),
            OrgFieldsNames.FORENSICS_AND_EDR.value: True,
            OrgFieldsNames.VULNERABILITY.value: True,
            OrgFieldsNames.SERVERS_LICENCES.value: self.get_servers_licences_capacity(from_cache=True),
            OrgFieldsNames.WORK_STATION_LICENCES.value: self.get_works_station_licences_capacity(from_cache=True),
            OrgFieldsNames.IOT_LICENCES.value: self.get_iot_licences_capacity(from_cache=True)
        }
        updated_data[OrgFieldsNames.FORENSICS.value] = updated_data[OrgFieldsNames.FORENSICS_AND_EDR.value]
        updated_data[OrgFieldsNames.EDR.value] = updated_data[OrgFieldsNames.FORENSICS_AND_EDR.value]
        for field_name, new_value in new_fields:
            logger.info(f"Update {field_name} from {updated_data[field_name]} to {new_value}")
            updated_data[field_name] = new_value
        self._rest_client.organizations.update_organization(current_org_name=current_name, data=updated_data,
                                                            expected_status_code=expected_status_code)
        if expected_status_code == 200:
            self._validate_updated_fields(new_fields=new_fields)

    def __repr__(self):
        return f"Organization {self.get_name(from_cache=True)}"


def get_default_org_expiration_date():
    org_fields = get_organization_fields_by_name(organization_name=DEFAULT_ORGANIZATION_NAME, safe=False)
    expiration_date = org_fields[OrgFieldsNames.EXPIRATION_DATE.value]
    expiration_date = StringUtils.get_txt_by_regex(text=expiration_date, regex=r'(\d+-\d+-\d+)', group=1)
    return expiration_date


def get_organization_fields_by_name(organization_name, safe=False) -> dict:
    """ When creating new organization (POST) the response doesn't contain any data, only status code,
    so use this to get the rest data in order to initialize the organization instance """
    all_organizations_fields = ADMIN_REST().organizations.get_all_organizations()
    for org_fields in all_organizations_fields:
        if org_fields[OrgFieldsNames.ORG_NAME.value] == organization_name:
            logger.debug(f"Organization '{organization_name}' updated data from management: \n {org_fields}")
            return org_fields
    assert safe, f"Organization {organization_name} was not found"
    logger.debug(f"Organization {organization_name} was not found")
    return None


def is_organization_exist_by_name(organization_name):
    org_fields = get_organization_fields_by_name(organization_name=organization_name, safe=True)
    if org_fields is None:
        return False
    else:
        return True


def _compare_new_org_data(expected_data: dict, actual_data: dict):
    """ Validate that organization actually created with the desired fields """
    name = expected_data[OrgFieldsNames.ORG_NAME.value]
    logger.info(f"Validate that organization {name} created with the correct values as were passed")
    not_relevant_fields = [OrgFieldsNames.REGISTRATION_PASSWORD.value, OrgFieldsNames.PASSWORD_CONFIRMATION.value]
    is_contains_forensicandedr_field = OrgFieldsNames.FORENSICS_AND_EDR.value in actual_data
    for field_name, expected_value in expected_data.items():
        if field_name not in not_relevant_fields:
            # in newer version of 5.2.0, forensicsAndEDR section was split into forensics and edr fields so needs to
            # validate which of the sections we need to use
            if (
                    field_name in [OrgFieldsNames.FORENSICS.value, OrgFieldsNames.EDR.value]
                    and is_contains_forensicandedr_field
            ):
                continue
            elif field_name == OrgFieldsNames.FORENSICS_AND_EDR.value and not is_contains_forensicandedr_field:
                continue
            if field_name == OrgFieldsNames.EXPIRATION_DATE.value:
                expected_value = StringUtils.get_txt_by_regex(text=expected_value, regex=r'(\d+-\d+-\d+)', group=1)
                actual_value = StringUtils.get_txt_by_regex(text=actual_data[field_name], regex=r'(\d+-\d+-\d+)',
                                                            group=1)
            else:
                actual_value = actual_data[field_name]
            assert actual_value == expected_value, \
                f"Org {name} not created successfully: {field_name} is {actual_value} instead of {expected_value}"
