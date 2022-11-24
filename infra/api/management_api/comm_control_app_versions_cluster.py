import logging
from typing import List
import allure
from infra.api import RestCommands
from infra.api.management_api.base_comm_control_app import BaseCommControlApp, ApplicationFieldsNames,\
    ApplicationPolicyAction

logger = logging.getLogger(__name__)


class CommControlAppVersionsCluster(BaseCommControlApp):
    """ A wrapper of our internal rest client for working with a cluster of all the installed versions.
           Each application will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)

    def __repr__(self):
        return f"A cluster of all the installed versions {self.name}, in organization' " \
               f"{self.get_organization_name(from_cache=True)}'"

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        """
        1. get all application
        2. find the representation of the cluster is version is empty
        """
        rest_client = rest_client or self._rest_client
        applications_fields = rest_client.comm_control.get_applications()
        for application_fields in applications_fields:
            if application_fields[ApplicationFieldsNames.PRODUCT.value] == self.name and \
                    not application_fields[ApplicationFieldsNames.VERSION.value]:
                logger.debug(f"{self} updated data from management: \n {application_fields}")
                if update_cache_data:
                    self.cache = application_fields
                return application_fields
        assert safe, f"A cluster of all the installed versions with name {self.name} was not found"
        logger.debug(f"A cluster of all the installed versions with name {self.name} was not found")
        return None

    @allure.step("Deny policy {policy_name} in all versions")
    def deny_policy_in_all_versions(self, policy_name: str, safe=False, wait=True, wait_sec=None):
        self.deny_policies_in_all_versions(policy_names=[policy_name], safe=safe, wait=wait,
                                           wait_sec=wait_sec)

    @allure.step("Allow policy {policy_name} in all versions")
    def allow_policy_in_all_versions(self, policy_name: str, safe=False, wait=True, wait_sec=None):
        self.allow_policies_in_all_versions(policy_names=[policy_name], safe=safe, wait=wait,
                                            wait_sec=wait_sec)

    @allure.step("Deny policies {policy_names} in all versions")
    def deny_policies_in_all_versions(self, policy_names: list[str], safe=False, wait=True, wait_sec=None):
        versions = self._get_all_versions(application_name=self.name)
        self.set_policies_permission(policy_names=policy_names, versions=versions, permission=ApplicationPolicyAction.DENY.value,
                                     safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Allow policies {policy_names} in all versions")
    def allow_policies_in_all_versions(self, policy_names: list[str], safe=False, wait=True, wait_sec=None):
        versions = self._get_all_versions(application_name=self.name)
        self.set_policies_permission(policy_names=policy_names, versions=versions, permission=ApplicationPolicyAction.ALLOW.value,
                                     safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Resolve application in all versions")
    def resolve(self, safe=False, wait=True, wait_sec=None):
        versions = self._get_all_versions(application_name=self.name)
        self.resolve_or_unresolve(to_resolve=True, versions=versions,
                                  safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Unresolve application in all versions")
    def unresolve(self, safe=False, wait=True, wait_sec=None):
        versions = self._get_all_versions(application_name=self.name)
        self.resolve_or_unresolve(to_resolve=False, versions=versions,
                                  safe=safe, wait=wait, wait_sec=wait_sec)

    def _get_all_versions(self, application_name) -> List[str]:
        versions = []
        applications_fields = self._rest_client.comm_control.get_applications()
        for application_fields in applications_fields:
            if application_fields[ApplicationFieldsNames.PRODUCT.value] == application_name and\
                    len(application_fields[ApplicationFieldsNames.VERSION.value]):
                versions.append(application_fields[ApplicationFieldsNames.VERSION.value])
        if len(versions):
            return versions





