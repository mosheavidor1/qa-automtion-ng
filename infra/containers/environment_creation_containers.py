from typing import List

from infra.enums import ComponentType


class MachineType:
    def __init__(self, cpu_count: int = 8,
                 memory_limit: int = 8000,
                 disk_size: int = 40000,
                 disk_type: str = 'ssd'):
        self.CPUCount = cpu_count
        self.MemoryLimit = memory_limit
        self.DiskSize = disk_size
        self.DiskType = disk_type


class EnvironmentSystemComponent:

    def __init__(self,
                 component_type: ComponentType,
                 component_version: str,
                 machine_type: MachineType):

        self.ComponentType = component_type.value
        self.ComponentVersion = component_version
        self.MachineType = machine_type


class DeployedEnvInfo:
    def __init__(self,
                 env_id: str,
                 components_created: List[dict],
                 registration_password: str,
                 admin_user: str,
                 admin_password: str,
                 rest_api_user: str,
                 rest_api_password: str,
                 location: str,
                 customer_name: str,
                 timezone: str,
                 installation_type: str,
                 environment_pool: str,
                 error_description: str):
        self._env_id = env_id
        self._components_created = components_created
        self._registration_password = registration_password
        self._admin_user = admin_user
        self._admin_password = admin_password
        self._rest_api_user = rest_api_user
        self._rest_api_password = rest_api_password
        self._location = location
        self._customer_name = customer_name
        self._timezone = timezone
        self._installation_type = installation_type
        self._environment_pool = environment_pool
        self._error_description = error_description

    def get_as_dict(self):
        return {
            'env_id': self._env_id,
            'components_created': self._components_created,
            'registration_password': self._registration_password,
            'admin_user': self._admin_user,
            'admin_password': self._admin_password,
            'rest_api_user': self._rest_api_user,
            'rest_api_password': self._rest_api_password,
            'location': self._location,
            'customer_name': self._customer_name,
            'timezone': self._timezone,
            'installation_type': self._installation_type,
            'environment_pool': self._environment_pool,
            'error_description': self._error_description,
        }

    @property
    def management_ip(self):
        if self._components_created is None:
            return None

        if len(self._components_created) == 0:
            return None

        for comp in self._components_created:
            if comp.get('ComponentType') == 'both' or comp.get('ComponentType' == 'manager'):
                return comp.get('MachineIp')

        return None

    @property
    def aggregator_ips(self):
        ips = []
        if self._components_created is None:
            return None

        if len(self._components_created) == 0:
            return None

        for comp in self._components_created:
            if comp.get('ComponentType') == 'both' or comp.get('ComponentType') == 'aggregator':
                ips.append(comp.get('MachineIp'))

        return ips

    @property
    def env_id(self):
        return self._env_id

    @property
    def components_created(self):
        return self._components_created

    @property
    def registration_password(self):
        return self._registration_password

    @property
    def admin_user(self):
        return self._admin_user

    @property
    def admin_password(self):
        return self._admin_password

    @property
    def rest_api_user(self):
        return self._rest_api_user

    @property
    def rest_api_password(self):
        return self._rest_api_password

    @property
    def location(self):
        return self._location

    @property
    def customer_name(self):
        return self._customer_name

    @property
    def timezone(self):
        return self._timezone

    @property
    def installation_type(self):
        return self._installation_type

    @property
    def environment_pool(self):
        return self._environment_pool

    @property
    def error_description(self):
        return self._error_description
