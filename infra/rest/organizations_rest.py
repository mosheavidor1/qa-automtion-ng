import json

import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.allure_report_handler.reporter import Reporter
from infra.containers.management_api_body_containers import CreateOrganizationRestData, OrganizationRestData
from infra.rest.base_rest_functionality import BaseRestFunctionality
from infra.utils.utils import JsonUtils


class OrganizationsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Get specific organization data: {organization_name}")
    def get_specific_organization_data(self,
                                       organization_name: str) -> dict | None:
        all_orgs = self.get_all_organizations(expected_status_code=200)
        for single_org in all_orgs:
            if single_org.get('name') == organization_name:
                Reporter.attach_str_as_file(file_name='organization data',
                                            file_content=json.dumps(single_org,
                                                                    indent=4))
                return single_org

        return None

    @allure.step("Get all organizations")
    def get_all_organizations(self, expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.organizations.ListOrganizations()

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List organizations - expected response code: {expected_status_code}, actual: {response.status_code}")

        as_dict = json.loads(response.content)
        return as_dict

    @allure.step("Create organization")
    def create_organization(self,
                            organization_data: CreateOrganizationRestData,
                            expected_status_code: int = 200):

        data = json.loads(JsonUtils.object_to_json(obj=organization_data,
                                                   null_sensitive=True))

        status, response = self._rest.passthrough.ExecuteRequest(url='/organizations/create-organization',
                                                                 mode='post',
                                                                 body=data,
                                                                 inputParams=None)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Create-organization - expected response code: {expected_status_code}, actual: {response.status_code}")

    @allure.step("Update organization")
    def update_organization(self,
                            organization_data: OrganizationRestData,
                            expected_status_code: int = 200):

        json_as_str = JsonUtils.object_to_json(obj=organization_data,
                                               null_sensitive=True)
        data = json.loads(json_as_str)

        status, response = self._rest.passthrough.ExecuteRequest(
            url=f'/organizations/update-organization?organization={organization_data.name}',
            mode='put',
            body=data,
            inputParams=None)

        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"Update-organization - expected response code: {expected_status_code}, actual: {response.status_code}")

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
