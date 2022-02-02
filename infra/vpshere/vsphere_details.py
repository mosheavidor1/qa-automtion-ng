"""
This file holds details of the clusters.
The variables of the clusters are objects representing the clusters.
"""

__author__ = "Dmitry Banny"


class Credentials:
    API_KEY = None


class Constants:
    MAX_DEPTH = 10
    TIMEOUT = 1500
    

class Cluster:
    """ Clusters information.
    
    The information is stored in dict structure:
        1. ensilo_vcsa10 - Dev environment
        2. ensilo_vcsa20 - General automation
        3. ensilo_vcsa30 - Malware environment
        4. ensilo_vcsa40 - General automation and performance

    Usage:
        import vsphere_config
        Ensilo_vcsa1.vhost
        Ensilo_vcsa1.name
        Ensilo_vcsa1.resource_pools
        Ensilo_vcsa1.datastore_name
    """
    def __init__(self, vhost, name, resource_pools, datastore_name):
        self._vhost = vhost
        self._name = name
        self._resource_pools = resource_pools
        self._datastore_name = datastore_name

    @property
    def cluster_vhost(self):
        return self._vhost

    @property
    def cluster_name(self):
        return self._name

    @property
    def cluster_resources_pool(self):
        return self._resource_pools

    @property
    def cluster_datastore_name(self):
        return self._datastore_name


Ensilo_vcsa10 = Cluster("10.51.100.110", "Ensilo_vcsa10", ["VT13-Testing"], "loc-vt13-r10-d1")

Ensilo_vcsa20 = Cluster("10.51.100.120", "Ensilo_vcsa20", ["QA22", "QA23"], "loc-vt22-r10-d1")

Ensilo_vcsa30 = Cluster("10.51.100.130", "Ensilo_vcsa30", ["QA", "QA41"], "loc-vt31-r10-d1")

Ensilo_vcsa40 = Cluster("ens-vcsa40.ensilo.local", "Ensilo_vcsa40", ["QA41", "SW42"], "loc-vt41-r10-d1")