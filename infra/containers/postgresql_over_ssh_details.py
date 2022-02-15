class PostgresqlOverSshDetails:

    def __init__(self,
                 db_name: str,
                 user_name: str,
                 password: str,
                 server_ip: str = '127.0.0.1',
                 server_port: int = 5432):

        self._db_name = db_name
        self._user_name = user_name
        self._password = password

        self._server_ip = server_ip
        self._server_port = server_port

    @property
    def db_name(self):
        return self._db_name

    @property
    def user_name(self):
        return self._user_name

    @property
    def password(self):
        return self._password

    @property
    def server_ip(self):
        return self._server_ip

    @property
    def server_port(self):
        return self._server_port
