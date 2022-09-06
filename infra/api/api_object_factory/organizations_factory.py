from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.organization import (
    Organization, OrgFieldsNames, DEFAULT_ORGANIZATION_NAME, MANAGEMENT_REGISTRATION_PASSWORD
)
import logging
import allure
from infra.api import ADMIN_REST
logger = logging.getLogger(__name__)


class OrganizationsFactory(BaseApiObjFactory):
    """ Find/Create organizations and return them as rest objects.
    1. The factory's rest credentials will be set as the default auth of each of the returned
        organization objects so these credentials should be the credentials of the tenant's default local admin user
    2. Organizations factory is by use only for tenant because tenant represents organization.
    3. When searching for organizations we must add the password because
    the organizations get api doesn't return the password """

    def __init__(self, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)

    def get_by_name(self, org_name: str, registration_password: str, safe=False):
        """ Find organization by name and return its rest api wrapper with the given password """
        organizations = self.get_by_field(field_name=OrgFieldsNames.ORG_NAME.value, value=org_name,
                                          registration_password=registration_password)
        if organizations is None:
            assert safe, f"Organizations with name '{org_name}' were not found"
            logger.debug(f"Organizations with name '{org_name}' were not found")
            return None
        assert len(organizations) == 1, f"These organizations have the same name ! \n {organizations}"
        return organizations[0]

    def get_by_field(self, field_name, value, registration_password):
        """ Get organizations by field """
        organizations = []
        logger.debug(f"Find organizations with field {field_name} = {value} ")
        all_orgs_fields = ADMIN_REST().organizations.get_all_organizations()
        for org_fields in all_orgs_fields:
            if org_fields[field_name] == value:
                org = Organization(rest_client=self._factory_rest_client, password=registration_password,
                                   initial_data=org_fields)
                organizations.append(org)
        if len(organizations):
            logger.debug(f"Found these Organizations with field {field_name}={value}: \n {organizations}")
            return organizations
        return None

    @allure.step("Create new organization")
    def create_organization(self, organization_name, password,
                            expected_status_code=200, **optional_data) -> Organization:
        """ Create new organization with the given password and the factory's rest credentials """
        logger.info(f"Create new organization '{organization_name}'")
        organization = Organization.create(rest_client=self._factory_rest_client, name=organization_name,
                                           password=password, expected_status_code=expected_status_code,
                                           **optional_data)
        return organization


def get_default_organization():
    """ Return the default organization, the default organization has admin credentials because
        it is under admin user """
    logger.debug(f"Get the default organization: {DEFAULT_ORGANIZATION_NAME}")
    organizations_factory = OrganizationsFactory(factory_rest_client=ADMIN_REST())
    default_organization = organizations_factory.get_by_name(org_name=DEFAULT_ORGANIZATION_NAME,
                                                             registration_password=MANAGEMENT_REGISTRATION_PASSWORD)
    return default_organization
