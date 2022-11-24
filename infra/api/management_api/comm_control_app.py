import logging
import allure
from infra.api import RestCommands
from infra.api.management_api.base_comm_control_app import BaseCommControlApp, ApplicationFieldsNames\
    , ApplicationPolicyAction

logger = logging.getLogger(__name__)


class CommControlApp(BaseCommControlApp):
    """ A wrapper of our internal rest client for working with Comm control application with a specific version.
           Each application will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._version = initial_data[ApplicationFieldsNames.VERSION.value]  # Static, unique identifier

    def __repr__(self):
        return f"Comm control application {self.name} in version {self.version} " \
               f"in organization '{self.get_organization_name(from_cache=True)}'"

    @property
    def version(self) -> str:
        return self._version

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        """ find the fields of the app with a specific version """
        rest_client = rest_client or self._rest_client
        applications_fields = rest_client.comm_control.get_applications()
        for application_fields in applications_fields:
            if application_fields[ApplicationFieldsNames.PRODUCT.value] == self.name and \
                    application_fields[ApplicationFieldsNames.VERSION.value] == self.version:
                logger.debug(f"{self} updated data from management: \n {application_fields}")
                if update_cache_data:
                    self.cache = application_fields
                return application_fields
        assert safe, f"Comm control application with name {self.name} in version {self.version} was not found"
        logger.debug(f"Comm control application with name {self.name} un version {self.version} was not found")
        return None

    @allure.step("Deny policy {policy_name}")
    def deny_policy(self, policy_name: str, safe=False, wait=True, wait_sec=None):
        self.deny_policies(policy_names=[policy_name], safe=safe, wait=wait,
                           wait_sec=wait_sec)

    @allure.step("Allow policy {policy_name}")
    def allow_policy(self, policy_name: str, safe=False, wait=True, wait_sec=None):
        self.allow_policies(policy_names=[policy_name], safe=safe, wait=wait,
                            wait_sec=wait_sec)

    @allure.step("Deny policies {policy_names}")
    def deny_policies(self, policy_names: list[str], safe=False, wait=True, wait_sec=None):
        self.set_policies_permission(policy_names=policy_names, versions=self.version,
                                     permission=ApplicationPolicyAction.DENY.value,
                                     safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Allow policies {policy_names}")
    def allow_policies(self, policy_names: list[str], safe=False, wait=True, wait_sec=None):
        self.set_policies_permission(policy_names=policy_names, versions=self.version,
                                     permission=ApplicationPolicyAction.ALLOW.value,
                                     safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Set policy {policy_name} permission to {permission}")
    def set_policy_permission(self, policy_name: str, permission, safe=False, wait=True, wait_sec=None):
        self.set_policies_permission(policy_names=[policy_name], versions=self.version,
                                     permission=permission,
                                     safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Resolve application")
    def resolve(self, wait=True, wait_sec=None, safe=False):
        self.resolve_or_unresolve(to_resolve=True, versions=self.version,
                                  safe=safe, wait=wait, wait_sec=wait_sec)

    @allure.step("Unresolve application")
    def unresolve(self, wait=True, wait_sec=None, safe=False):
        self.resolve_or_unresolve(to_resolve=False, versions=self.version,
                                  safe=safe, wait=wait, wait_sec=wait_sec)



