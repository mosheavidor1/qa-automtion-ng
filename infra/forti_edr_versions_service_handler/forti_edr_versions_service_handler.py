import allure

import third_party_details
from infra.enums import HttpRequestMethodsEnum
from infra.utils.utils import HttpRequesterUtils


class FortiEdrVersionsServiceHandler:

    @staticmethod
    @allure.step('Extract latest versions from dedicated service of the base version: {base_version}')
    def get_latest_components_builds(base_version: str, num_builds: int = 1):
        """
        This method returns the latest builds of various system components according to base version.
        it sends request to service which provide this information on a "automation services machine"
        :param base_version: for example 5.2.0
        :param num_build: number of required latest builds, 1 is the default and will return the latest build
        :return: dictionary with latest build of the various system components.
        """
        if base_version.count('.') != 2:
            assert False, "Incorrect template of base version, insert something such as 5.1.0 (x.y.z)"

        url = f'http://{third_party_details.AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{third_party_details.LATEST_VERSIONS_SERVICE_PORT}/latest_build?base_version={base_version}&num_builds={num_builds}'
        versions_dict = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                        url=url,
                                                        expected_status_code=200)
        return versions_dict

    @staticmethod
    @allure.step("Extract last {num_last_content_files} content files from shared folder")
    def get_latest_content_files_from_shared_folder(num_last_content_files: int = 1):
        url = f'http://{third_party_details.AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{third_party_details.LATEST_VERSIONS_SERVICE_PORT}/list_content?num_last_content_files={num_last_content_files}'
        versions_dict = HttpRequesterUtils.send_request(request_method=HttpRequestMethodsEnum.GET,
                                                        url=url,
                                                        expected_status_code=200)
        return versions_dict


