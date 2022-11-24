import random
import time
from contextlib import contextmanager

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


@contextmanager
def execute_remote_command_via_ps_py_exec_context(host_ip: str,
                                                  user_name: str,
                                                  password: str,
                                                  cmd: str,
                                                  timeout: int = 180,
                                                  asynchronous: bool = False):
    created_service_on_remote_machine = False
    try:
        connection = PsPyExecClientWrapper(host_ip,
                                           unique_connection_id=random.randint(1000000, 9999999),
                                           username=user_name,
                                           password=password,
                                           encrypt=True)
        connection.connect()
        time.sleep(1)
        connection.create_service()
        created_service_on_remote_machine = True
    except:
        connection = PsPyExecClientWrapper(host_ip,
                                           unique_connection_id=random.randint(1000000, 9999999),
                                           username=user_name,
                                           password=password,
                                           encrypt=True)
        connection.connect()
        time.sleep(1)
        connection.create_service()
        created_service_on_remote_machine = True

    finally:
        if not created_service_on_remote_machine:
            f"Failed to create PAExec service on remote windows machine {host_ip}"

    stdout, stderr_err, status_code = connection.run_executable("cmd.exe",
                                                                arguments=f'/c {cmd}',
                                                                timeout_seconds=timeout,
                                                                asynchronous=asynchronous,
                                                                use_system_account=True)
    if asynchronous:
        yield None, None, None
    else:
        yield stdout.decode('utf-8'), stderr_err.decode('utf-8'), status_code

    try:
        connection.remove_service()
        connection.disconnect()
    except:
        # we only trying to remove the serivce and disconnect, it's not worth to fail if we failed with this operation
        pass
    finally:
        if connection is not None:
            del connection


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
