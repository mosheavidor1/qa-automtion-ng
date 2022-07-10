from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.api.nslo_wrapper.base_rest_functionality import BaseRestFunctionality






def trigger_events(self):
    dns_query = 'nslookup google.com'
    self.os_station.execute_cmd(dns_query)


def test_dns_query(self):
    category = "Network"
    query = f"Type: \"DNS Query\" AND Time:>{self.start_time}"





