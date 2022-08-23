import json
import logging
from typing import List
import allure
from ensilo.platform.rest.nslo_management_rest import NsloRest
from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality
logger = logging.getLogger(__name__)


class IpSetsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)

    @allure.step("Update exsist IP set")
    def update_exist_ip_set(self, name, ip_set_data: dict, expected_status_code: int = 200):
        logger.info(f"update exsist IP set with this data :\n {ip_set_data} \n expected: {expected_status_code}")
        status, response = self._rest.ipsets.UpdateIpSet(name=name, **ip_set_data)
        assert status, response
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List ip sets - expected response code: {expected_status_code}, actual: {response.status_code}")

    @allure.step("Define new IP set")
    def define_new_ip_set(self, name, ip_set_data: dict, expected_status_code: int = 200):
        logger.info(f"Create new ip set with this data :\n {ip_set_data} \n expected: {expected_status_code}")
        status, response = self._rest.ipsets.CreateIpSet(name=name, **ip_set_data)
        err_msg = f"Failed to create ip set, got {response.status_code} instead of {expected_status_code}"
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code, error_message=err_msg)

    def get_ip_sets(self, ip=None, expected_status_code: int = 200) -> List[dict]:
        status, response = self._rest.ipsets.ListIpSets(ip=ip)
        assert status, f'Could not get response from the management. \n{response}'
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List ip sets - expected response code: {expected_status_code}, actual: {response.status_code}")

        ip_sets = json.loads(response.content)
        return ip_sets

    @allure.step("Delete IP set")
    def delete_ip_set(self, name, organization=None, expected_status_code=200):
        logger.info(f"update exsist IP set")
        status, response = self._rest.ipsets.DeleteIpSet(ipSets=name, organization=organization)
        self._validate_expected_status_code(expected_status_code=expected_status_code,
                                            actual_status_code=response.status_code,
                                            error_message=f"List ip sets - expected response code: {expected_status_code}, actual: {response.status_code}")

