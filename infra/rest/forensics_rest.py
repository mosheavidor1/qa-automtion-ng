from ensilo.platform.rest.nslo_management_rest import NsloRest

from infra.rest.base_rest_functionality import BaseRestFunctionality


class ForensicsRest(BaseRestFunctionality):

    def __init__(self, nslo_rest: NsloRest):
        super().__init__(nslo_rest=nslo_rest)