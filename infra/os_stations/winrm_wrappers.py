import time

from winrm import Protocol, Session, Response
from winrm.exceptions import WinRMOperationTimeoutError


class ProtocolWinrmWrapper(Protocol):

    def get_command_output_with_timeout(self, shell_id, command_id, timeout):
        """
        Get the Output of the given shell and command
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command_id: The command id on the remote machine.
         See #run_command
        #@return [Hash] Returns a Hash with a key :exitcode and :data.
         Data is an Array of Hashes where the cooresponding key
        #   is either :stdout or :stderr.  The reason it is in an Array so so
         we can get the output in the order it ocurrs on
        #   the console.
        """
        stdout_buffer, stderr_buffer = [], []
        command_done = False
        start_time = time.time()
        while not command_done and time.time() - start_time < timeout:
            try:
                stdout, stderr, return_code, command_done = \
                    self._raw_get_command_output(shell_id, command_id)
                stdout_buffer.append(stdout)
                stderr_buffer.append(stderr)
            except WinRMOperationTimeoutError:
                # this is an expected error when waiting for a long-running process, just silently retry
                pass
        return b''.join(stdout_buffer), b''.join(stderr_buffer), return_code


class SessionWinrmWrapper(Session):

    def __init__(self, target, auth, **kwargs):
        username, password = auth
        super().__init__(target, auth, **kwargs)
        self.protocol = ProtocolWinrmWrapper(self.url,
                                             username=username,
                                             password=password,
                                             read_timeout_sec=180,
                                             **kwargs)

    def run_cmd_with_timeout(self, command, timeout, args=()):
        # TODO optimize perf. Do not call open/close shell every time

        if timeout is None or timeout < 1:
            raise ValueError('timeout value is wrong, should not be negative number')

        shell_id = self.protocol.open_shell()
        command_id = self.protocol.run_command(shell_id, command, args)
        rs = Response(self.protocol.get_command_output_with_timeout(shell_id, command_id, timeout))
        self.protocol.cleanup_command(shell_id, command_id)
        self.protocol.close_shell(shell_id)
        return rs
