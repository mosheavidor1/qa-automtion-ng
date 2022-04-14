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
                 components_created: str,
                 registration_password: str,
                 admin_user: str,
                 admin_password: str,
                 rest_api_user: str,
                 rest_api_password: str,
                 location: str,
                 environment_name: str,
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
        self._environment_name = environment_name
        self._timezone = timezone
        self._installation_type = installation_type
        self._environment_pool = environment_pool
        self._error_description = error_description

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
    def environment_name(self):
        return self._environment_name

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
