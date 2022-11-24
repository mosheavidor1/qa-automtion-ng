class LicenseStatus:

    def __init__(self,
                 workstation_in_use: int,
                 workstation_remaining: int,
                 servers_in_use: int,
                 servers_remaining: int):
        self._workstation_in_use = workstation_in_use
        self._workstation_remaining = workstation_remaining
        self._servers_in_use = servers_in_use
        self._servers_remaining = servers_remaining

    @property
    def workstation_in_use(self):
        return self._workstation_in_use

    @property
    def workstation_remaining(self):
        return self._workstation_remaining

    @property
    def servers_in_use(self):
        return self._servers_in_use

    @property
    def servers_remaining(self):
        return self._servers_remaining
