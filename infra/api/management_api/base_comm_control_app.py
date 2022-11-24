import time
from abc import abstractmethod
from enum import Enum
import logging
from typing import List
import allure

from infra.api import RestCommands
from infra.api.api_object import BaseApiObj
from infra.common_utils import WAIT_FOR_COLLECTOR_NEW_CONFIGURATION

logger = logging.getLogger(__name__)

WAIT_AFTER_RESOLVE_UN_RESOLVE = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION
WAIT_AFTER_SET_APPLICATION_MODE = WAIT_FOR_COLLECTOR_NEW_CONFIGURATION


class AppPolicyFieldsNames(Enum):
    DECISION = 'decision'
    POLICY_MODE = 'policyMode'
    POLICY_NAME = 'policyName'


class ApplicationFieldsNames(Enum):
    PRODUCT = 'product'
    VERSION = 'version'
    HANDLED = 'handled'
    COLLECTORS = 'collectors'
    COLLECTORS_GROUPS = 'collectorsGroup'
    ORGANIZATION = 'organization'
    DECISIONV2 = 'decisionv2'
    CVES = 'cves'
    PROCESSES = 'processes'
    RECOMMENDATION = 'recommendation'
    SEEN = 'seen'
    SEVERITY = 'severity'
    STATISTICS = 'statistics'
    VENDOR = 'vendor'
    FIRST_CONNECTION_TIME = 'firstConnectionTime'
    LAST_CONNECTION_TIME = 'lastConnectionTime'


class ApplicationPolicyAction(Enum):
    ALLOW = 'Allow'
    DENY = 'Deny'


class BaseCommControlApp(BaseApiObj):
    """ A wrapper of our internal rest client for working with Comm control application.
           Each application will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._name = initial_data[ApplicationFieldsNames.PRODUCT.value]

    @property
    def name(self) -> str:
        return self._name

    def get_organization_name(self, from_cache=None, update_cache=True) -> str:
        field_name = ApplicationFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_severity(self, from_cache=None, update_cache=True) -> str:
        field_name = ApplicationFieldsNames.SEVERITY.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def is_resolved(self, from_cache=None, update_cache=True) -> bool:
        field_name = ApplicationFieldsNames.HANDLED.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_policies(self, from_cache=None, update_cache=True) -> List[dict]:
        """ Search filed DECISIONV2 (get from rest API) """
        field_name = ApplicationFieldsNames.DECISIONV2.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_policy_by_name(self, policy_name, from_cache=None, update_cache=True) -> dict:
        policy = [policy for policy in self.get_policies(from_cache=from_cache, update_cache=update_cache)
                  if policy[AppPolicyFieldsNames.POLICY_NAME.value] == policy_name]
        return policy[0]

    def get_policy_permission(self, policy_name, from_cache=None, update_cache=True) -> str:
        policy = self.get_policy_by_name(policy_name=policy_name, from_cache=from_cache, update_cache=update_cache)
        return policy[AppPolicyFieldsNames.DECISION.value]

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

    def create(self):
        raise NotImplemented("Application can't be created")

    def update_fields(self, safe=False):
        raise NotImplemented("Not relevant")

    def _delete(self, expected_status_code=200):
        raise NotImplemented("Should be implemented, check which credentials are required")

    @abstractmethod
    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        pass

    @allure.step("Set application policies {policy_names} permission to {permission}")
    def set_policies_permission(self, policy_names: list[str], versions: str or List[str], permission: str, wait=True,
                                safe=False, wait_sec=None):
        is_in_expected_permission = all(self.get_policy_permission(policy_name=policy_name) == permission for policy_name in
                                        policy_names)
        wait_sec = wait_sec or WAIT_AFTER_SET_APPLICATION_MODE
        if is_in_expected_permission:
            assert safe, f"{self} in version {versions} policies {policy_names} already in {permission} permission!"
            logger.info(f"{self} in version {versions} policies {policy_names} already in {permission} permission!")
        else:
            logger.info(f"Set {self} in version {versions} policies {policy_names} to {permission} permission")
            self._rest_client.comm_control.set_applications_permission(policy_names=policy_names, applications=self.name,
                                                                       permission=permission, versions=versions)
            if wait:
                logger.info(f"Sleep {wait_sec} seconds after set application policies permission to {permission}")
                time.sleep(wait_sec)

    @allure.step("Resolve/Un-resolve application")
    def resolve_or_unresolve(self, to_resolve: bool, versions: str or List[str], wait=True, safe=False,
                             wait_sec=None):
        is_in_expected_mode = True if self.is_resolved() == to_resolve else False
        wait_sec = wait_sec or WAIT_AFTER_RESOLVE_UN_RESOLVE
        if is_in_expected_mode:
            assert safe, f"{self} in version {versions} already in {to_resolve} resolve!"
            logger.info(f"{self} in version {versions} already in {to_resolve} resolve!")
        else:
            logger.info(f"Set {self} in version {versions} to {to_resolve} resolve")
            self._rest_client.comm_control.resolve_or_unresolve_app(applications=self.name, to_resolve=to_resolve,
                                                                    versions=versions)
            if wait:
                logger.info(f"Sleep {wait_sec} seconds after resolve/unresolve application")
                time.sleep(wait_sec)
