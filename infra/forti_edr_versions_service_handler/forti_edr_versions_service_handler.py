import allure

import third_party_details
from infra.enums import HttpRequestMethodsEnum
from infra.utils.utils import HttpRequesterUtils


class FortiEdrVersionsServiceHandler:

    @staticmethod
    @allure.step('Extract latest versions from dedicated service of the base version: {base_version}')
    def get_latest_versions(base_version):
        if base_version.count('.') != 2:
            assert False, "Incorrect template of base version, insert something such as 5.1.0 (x.y.z)"

        url = f'http://{third_party_details.AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{third_party_details.LATEST_VERSIONS_SERVICE_PORT}/latest_build?base_version={base_version}'
        versions_dict = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                        url=url,
                                                        expected_status_code=200)
        return versions_dict