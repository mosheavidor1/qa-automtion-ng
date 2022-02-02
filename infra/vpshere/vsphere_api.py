import requests
import vsphere_details
from pyVim.connect import SmartConnectNoSSL


class VsphereOperation:
    def __init__(self, connection_object: object):
        self.connection = connection_object
        
        
    def create_session(self):
        _path = ""
    
    def get_all_vms(self):
        pass

    def get_all_vms_extended(self):
        pass
