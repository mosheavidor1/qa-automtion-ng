import json
from typing import List
import logging
import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.allure_report_handler.reporter import Reporter
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality

logger = logging.getLogger(__name__)


class OrganizationsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    def get_all_organizations(self, expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.organizations.ListOrganizations()

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List organizations - expected response code: {expected_status_code}, actual: {response.status_code}")

        as_dict = json.loads(response.content)
        return as_dict

    @allure.step("Create organization")
    def create_organization(self, org_data: dict, expected_status_code=200):
        logger.info(f"Create new org with this data :\n {org_data} \n expect: {expected_status_code}")
        status, response = self._rest.passthrough.ExecuteRequest(url='/organizations/create-organization',
                                                                 mode='post',
                                                                 body=org_data,
                                                                 inputParams=None)
        err_msg = f"Failed to create new organization, got {response.status_code} instead of {expected_status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code, error_message=err_msg)

    @allure.step("Update organization")
    def update_organization(self, current_org_name, data: dict, expected_status_code=200):
        logger.info(f"Update org '{current_org_name}' with this data :\n {data} \n expected: {expected_status_code}")
        status, response = self._rest.passthrough.ExecuteRequest(
            url=f'/organizations/update-organization?organization={current_org_name}', mode='put', body=data,
            inputParams=None)
        err_msg = f"Failed to update organization, got {response.status_code} instead of {expected_status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code, error_message=err_msg)

    @allure.step("Delete organization")
    def delete_organization(self,
                            organization_name: str,
                            expected_status_code: int = 200):

        status, response = self._rest.passthrough.ExecuteRequest(
            url=f'/organizations/delete-organization?organization={organization_name}',
            mode='delete',
            body=None,
            inputParams=None)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Delete-organization - expected response code: {expected_status_code}, actual: {response.status_code}")

