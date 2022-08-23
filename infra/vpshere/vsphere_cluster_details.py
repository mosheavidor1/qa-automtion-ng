"""
This file holds details of the clusters.
The variables of the clusters are objects representing the clusters.
"""

__author__ = "Dmitry Banny"

from typing import List


class Credentials:
    API_KEY = None


class Constants:
    MAX_DEPTH = 10
    TIMEOUT = 1500
    

class ClusterDetails:
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
    def __init__(self, vhost: str, name: str, resource_pools: List[str], datastore_name: str, malware: bool=False):
        self._vhost = vhost
        self._name = name
        self._resource_pools = resource_pools
        self._datastore_name = datastore_name
        self._malware = malware

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

    @property
    def malware(self):
        return self._malware


ENSILO_VCSA_10 = ClusterDetails(
    vhost="ens-vcsa10.ensilo.local", name="Ensilo_vcsa10",
    resource_pools=["VT13-Testing"], datastore_name="loc-vt13-r10-d1"
)

ENSILO_VCSA_20 = ClusterDetails(
    vhost="ens-vcsa20.ensilo.local", name="Ensilo_vcsa20",
    resource_pools=["QA22", "QA23"], datastore_name="loc-vt22-r10-d1"
)

ENSILO_VCSA_30 = ClusterDetails(
    vhost="ens-vcsa30.ensilo.local", name="Ensilo_vcsa30",
    resource_pools=["QA", "QA41"], datastore_name="loc-vt31-r10-d1"
)

ENSILO_VCSA_40 = ClusterDetails(
    vhost="ens-vcsa40.ensilo.local", name="Ensilo_vcsa40",
    resource_pools=["QA41", "SW42"], datastore_name="loc-vt41-r10-d1"
)
