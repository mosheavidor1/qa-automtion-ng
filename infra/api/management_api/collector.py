import logging
from enum import Enum
from infra.api.api_object import BaseApiObj
from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.enums import FortiEdrSystemState
from infra.common_utils import wait_for_condition
from infra.system_components.collectors.default_values import COLLECTOR_KEEPALIVE_INTERVAL, MAX_WAIT_FOR_STATUS, \
    MAX_WAIT_FOR_DELETION
import allure
logger = logging.getLogger(__name__)


class CollectorFieldsNames(Enum):
    """ Collector's fields names as we get from server """
    IP = 'ipAddress'
    ID = 'id'
    COLLECTOR_NAME = 'name'
    GROUP_NAME = 'collectorGroupName'
    OPERATING_SYSTEM = 'operatingSystem'
    LAST_SEEN = 'lastSeenTime'
    MAC = 'macAddresses'
    ACCOUNT_NAME = 'accountName'
    ORGANIZATION = 'organization'
    STATE = 'state'
    OS_FAMILY = 'osFamily'
    STATE_ADDITIONAL_INFO = 'stateAdditionalInfo'
    VERSION = 'version'
    LOGGED_USERS = 'loggedUsers'
    SYSTEM_INFORMATION = 'systemInformation'


class RestCollector(BaseApiObj):
    """ A wrapper for our internal nslo wrapper that holds all the collector's data from the server
    (cached and option to get updated fields) and contains all capabilities that we can
    perform on the collector from server.
    1. Collector can't be created/edit fields via mgmt, that's why we don't have 'update fields'/ 'create' methods.
    3. The rest credentials are user's rest (that passed via collectors factory) because actions on collectors
    are done via different users.
    4. Collector has a unique identifier = the device id (host ip & name can be changed during test) so we can monitor
    this object's life cycle with this unique id"""

    def __init__(self, rest_client: RestCommands, initial_data: dict):  # Need to pass rest client because each user have its own
        super().__init__(rest_client=rest_client, initial_data=initial_data)
        self._id = initial_data[CollectorFieldsNames.ID.value]  # Static, unique identifier

    def __repr__(self):
        return f"Rest Collector {self.id}: '{self.get_name(from_cache=True)}' on host '{self.get_ip(from_cache=True)}'"

    @property
    def id(self) -> int:
        return self._id

    def get_name(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.COLLECTOR_NAME.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_ip(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.IP.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_organization_name(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.ORGANIZATION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_group_name(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.GROUP_NAME.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_os_family(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.OS_FAMILY.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_operating_system(self, from_cache=None, update_cache=True) -> str:
        field_name = CollectorFieldsNames.OPERATING_SYSTEM.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_status(self, from_cache=None, update_cache=True):
        field_name = CollectorFieldsNames.STATE.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

    def get_version(self, from_cache=None, update_cache=True) -> str:
        field_name = CollectorFieldsNames.VERSION.value
        value = self._get_field(field_name=field_name, from_cache=from_cache, update_cache=update_cache)
        return value

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
        raise NotImplemented("Collector can't be created via management")

    def update_fields(self):
        raise NotImplemented("Collector can't be updated via management")

    def get_fields(self, safe=False, update_cache_data=False, rest_client=None) -> dict:
        rest_client = rest_client or self._rest_client
        collectors_fields = rest_client.system_inventory.get_collector_info_by_id(collector_id=self.id)
        if len(collectors_fields):
            assert len(collectors_fields) == 1
            collector_fields = collectors_fields[0]
            logger.debug(f"Collector {self} updated data from management: \n {collector_fields}")
            if update_cache_data:
                self._cache = collector_fields
            return collector_fields
        assert safe, f"Collector with id {self.id} was not found in MGMT"
        logger.debug(f"Collector with id {self.id} was not found in MGMT")
        return None

    def delete(self):
        """ Delete collector from management using user credentials """
        # Validate that uninstalled before delete ?
        # Afterwards validate deletion via the inherited method
        self._delete()

    def _delete(self):
        name = self.get_name()
        self._rest_client.system_inventory.delete_collectors(collector_names=[name])

    def uninstall(self):
        raise NotImplemented("Should be implemented")

    def export(self):
        raise NotImplemented("Should be implemented")

    @allure.step("Isolate collector")
    def isolate(self, wait=True, ):
        self._rest_client.system_inventory.isolate_collector_by_name_and_id(collector_name=self.get_name(),
                                                                            collector_id=self.id,
                                                                            organization_name=self.get_organization_name())

    @allure.step("Remove collector from isolation")
    def remove_from_isolation(self):
        self._rest_client.system_inventory.remove_isolation_from_collector(collector_name=self.get_name(),
                                                                           collector_id=self.id,
                                                                           organization_name=self.get_organization_name())

    def enable_or_disable(self):
        raise NotImplemented("Should be implemented")

    def is_disconnected(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.DISCONNECTED.value

    def is_degraded(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.DEGRADED.value

    def is_uninstalling(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.UNINSTALLING.value

    @allure.step("Wait until is Disconnected in management")
    def wait_until_disconnected(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is Disconnected in management")
        wait_for_condition(condition_func=self.is_disconnected, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is in disconnected state in management")

    @allure.step("Wait until is Degraded in management")
    def wait_until_degraded(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is degraded in management")
        wait_for_condition(condition_func=self.is_degraded, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is in Degraded state in management")

    @allure.step("Wait for status 'uninstalling' in management")
    def wait_for_uninstalling(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is in status 'uninstalling' in management")
        wait_for_condition(condition_func=self.is_uninstalling, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is in 'uninstalling' state in management")

    @allure.step("Wait until deleted from management")
    def wait_until_deleted(self, timeout_sec=MAX_WAIT_FOR_DELETION, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is deleted from management")
        wait_for_condition(condition_func=self.is_not_exist, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} does not appear in management")

    @allure.step("Enable collector")
    def enable(self):
        self._rest_client.system_inventory.toggle_collector(collector_name=self.get_name(from_cache=False),
                                                            organization_name=self.get_organization_name(
                                                                from_cache=False),
                                                            toggle_status=FortiEdrSystemState.ENABLED)

    def is_running(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.RUNNING.value

    def is_isolated(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.RUNNING.value

    @allure.step("Wait until running in management")
    def wait_until_running(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is running in management")
        wait_for_condition(condition_func=self.is_running, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is in 'running' state in management")

    @allure.step("Wait until isolated in management")
    def wait_until_isolated(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is isolated in management")
        wait_for_condition(condition_func=self.is_isolated, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is isolated in management")

    @allure.step("Disable collector")
    def disable(self):
        self._rest_client.system_inventory.toggle_collector(collector_name=self.get_name(from_cache=False),
                                                            organization_name=self.get_organization_name(from_cache=False),
                                                            toggle_status=FortiEdrSystemState.DISABLED)

    def is_disabled(self):
        return self.get_status(from_cache=False) == FortiEdrSystemState.DISABLED.value

    @allure.step("Wait until disabled in management")
    def wait_until_disabled(self, timeout_sec=MAX_WAIT_FOR_STATUS, interval_sec=COLLECTOR_KEEPALIVE_INTERVAL):
        logger.info(f"Wait until {self} is disabled in management")
        wait_for_condition(condition_func=self.is_disabled, timeout_sec=timeout_sec, interval_sec=interval_sec,
                           condition_msg=f"{self} is in 'disabled' state in management")

    def is_exist(self) -> bool:
        """ Check if collector exists in management """
        logger.info(f"Check if {self} exists")
        return self.get_fields(safe=True) is not None

    def is_not_exist(self) -> bool:
        """ Check if collector doesn't exist in management """
        logger.info(f"Check if {self} doesn't exist in management")
        return not self.is_exist()

    @allure.step("Move to different group in same organization")
    def move_to_different_group(self, target_group_name, expected_status_code: int = 200):
        current_group_name = self.get_group_name()
        assert target_group_name != current_group_name
        logger.info(f"Move {self} from group {current_group_name} to group {target_group_name} in same organization")
        self._rest_client.system_inventory.move_collector_to_group(collector_name=self.get_name(),
                                                                   group_name=target_group_name,
                                                                   expected_status_code=expected_status_code)
        updated_group_name = self.get_group_name(from_cache=False)
        assert updated_group_name == target_group_name, f"{self} didn't move to group: {target_group_name}"

