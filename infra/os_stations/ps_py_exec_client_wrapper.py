import random

from pypsexec.client import Client
import socket
import uuid
from smbprotocol.connection import (
    Connection
)

from smbprotocol.session import (
    Session
)

from pypsexec.paexec import (
    get_unique_id
)

from pypsexec.scmr import (
    Service
)


class PsPyExecClientWrapper(Client):

    def __init__(self, server, unique_connection_id, username=None, password=None, port=445,
                 encrypt=True):
        super().__init__(server=server, username=username, password=password, port=port, encrypt=encrypt)

        self.server = server
        self.port = port
        self.pid = unique_connection_id
        self.current_host = socket.gethostname()
        self.connection = Connection(uuid.uuid4(), server, port)
        self.session = Session(self.connection, username, password,
                               require_encryption=encrypt)

        self.service_name = "PAExec-%d-%s" % (self.pid, self.current_host)

        self._exe_file = "%s.exe" % self.service_name
        self._stdout_pipe_name = "PaExecOut%s%d" \
                                 % (self.current_host, self.pid)
        self._stderr_pipe_name = "PaExecErr%s%d" \
                                 % (self.current_host, self.pid)
        self._stdin_pipe_name = "PaExecIn%s%d" % (self.current_host, self.pid)
        self._unique_id = get_unique_id(self.pid, self.current_host)

        self._service = Service(self.service_name, self.session)
