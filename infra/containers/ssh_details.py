class SshDetails:

    def __init__(self,
                 host_ip: str,
                 user_name: str,
                 password: str,
                 port: int = 22):
        self._host_ip = host_ip
        self._user_name = user_name
        self._password = password
        self._port = port

    @property
    def host_ip(self):
        return self._host_ip

    @property
    def user_name(self):
        return self._user_name

    @property
    def password(self):
        return self._password

    @property
    def port(self):
        return self._port
