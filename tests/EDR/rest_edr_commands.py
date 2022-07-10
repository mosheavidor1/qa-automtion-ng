
from time import sleep
from ensilo.platform.rest.nslo_management_rest import NsloManagementConnection, NsloRest
from json import loads
import os
import json




class RestCommands(object):



 def edr2_search(self, **kwargs):
    body = {
        "category": "All",
        "devices": [],
        "facets": [],
        "filters": [],
        "itemsPerPage": 20,
        "offset": 0,
        "query": "",
        "time": "lastHour",
        "sorting": []
    }
    body.update(kwargs)
    status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/search", mode="post",
                                                            inputParams={},
                                                            body=body)
    json_data = json.loads(response.text)
    return json_data


def edr2_count(self, **kwargs):
    body = {
        "category": "All",
        "devices": [],
        "facets": [],
        "filters": [],
        "itemsPerPage": 20,
        "offset": 0,
        "query": "",
        "time": "lastHour",
        "sorting": []
    }
    body.update(kwargs)
    status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/counts", mode="post",
                                                            inputParams={},
                                                            body=body)
    json_data = json.loads(response.text)
    return json_data


def edr2_device_list(self, **kwargs):
    body = {
        "category": "All",
        "devices": [],
        "facets": [],
        "filters": [],
        "itemsPerPage": 20,
        "offset": 0,
        "time": "lastHour",
        "query": "",
        "sorting": []
    }
    body.update(kwargs)
    status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/device-list", mode="post",
                                                            inputParams={},
                                                            body=body)
    json_data = json.loads(response.text)
    return json_data


def edr2_facets(self, **kwargs):
    body = {
        "category": "All",
        "devices": [],
        "facets": [],
        "filters": [],
        "itemsPerPage": 20,
        "offset": 0,
        "query": "",
        "sorting": []
    }
    body.update(kwargs)
    status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/facets", mode="post",
                                                            inputParams={},
                                                            body=body)
    json_data = json.loads(response.text)
    return json_data


def edr2_schema(self):
    status, response = self.rest.passthrough.ExecuteRequest(url="/threat-hunting/schema", mode="get",
                                                            inputParams={})
    json_data = json.loads(response.text)
    return json_data