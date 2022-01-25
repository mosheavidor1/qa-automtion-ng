# Rewritten file 'connect.py'

import vsphere_config
import vsphere_management

__author__ = "Dmitry Banny"


class VsphereConnection(vsphere_config):
    """ This class provides a connection to a Vsphere """

    def __init__(self, username, password,  vm_name=None, malware=False):
        """Providing a connection information to a Vsphere is required.

        Parameters
        ----------
        password : str
            Password to connect to Vsphere
        username : str
            Username to connect to Vsphere
            Virtual machine name to use for manipulation
        malware : bool, optional
            Set to True is the environment is , by default False
        """
        self._password = password
        self._username = username
        self._vm_name = vm_name
        self._malware = malware

    def cluster(self):
        if self._malware:
            vsphere_obj = vsphere_management.VsphereMachine(vhost=Ensilo_vcsa30.vhost)
            return vsphere_obj
        else:
            pass

if __name__ == '__main__':
    print(vsphere_config.Ensilo_vcsa30)
    VsphereConnection("ensilo\\automation", "Aut0g00dqa42", "dima_colletor10x64").cluster()
