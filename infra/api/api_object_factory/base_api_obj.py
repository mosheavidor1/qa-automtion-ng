from abc import abstractmethod
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
logger = logging.getLogger(__name__)


class BaseApiObjFactory:
    """ Abstract base class for:
     1. Find component in management (via rest api) and return this component's rest api wrapper.
     2. Or Create new component in management (via rest api) and return this component's rest api wrapper """

    def __init__(self, factory_rest_client: RestCommands):
        self._factory_rest_client = factory_rest_client

    @abstractmethod
    def get_by_field(self, field_name, value):
        pass
