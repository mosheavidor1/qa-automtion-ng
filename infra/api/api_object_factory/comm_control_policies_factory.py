from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.management_api.base_policy import PolicyFieldsNames
from infra.api.management_api.comm_control_policy import CommControlPolicy
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
logger = logging.getLogger(__name__)


class CommControlPoliciesFactory(BaseApiObjFactory):
    """ Find comm control policies and return them as rest objects  with the user's credentials.
    The factory's rest credentials will be set as the default auth of each of the returned
    comm control policy objects so these credentials should be the credentials of a tested user """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_policy_by_name(self, policy_name, rest_client=None, safe=False) -> CommControlPolicy:
        rest_client = rest_client or self._factory_rest_client
        field_name = PolicyFieldsNames.NAME.value
        policies = self.get_by_field(field_name=field_name, value=policy_name, rest_client=rest_client,
                                     safe=safe)
        assert len(policies) == 1
        return policies[0]

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> List[CommControlPolicy]:
        """ Find comm control policies by field name<>value and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)"""
        policies = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find comm control policies with field {field_name} = {value} in organization {org_name}")
        policies_fields = rest_client.communication_control.get_policies()
        for policy_fields in policies_fields:
            if policy_fields[field_name] == value:
                policy = CommControlPolicy(rest_client=rest_client, initial_data=policy_fields)
                policies.append(policy)
        if len(policies):
            logger.debug(f"Found these comm control policies with field {field_name}={value}: \n {policies}")
            return policies
        assert safe, f"Didn't find any comm control policy with field {field_name}={value} in organization {self._organization_name}"
        logger.info(f"Didn't find any comm control policy with field {field_name}={value} in organization {self._organization_name}")
        return policies

    def get_policies(self, rest_client=None, safe=False) -> List[CommControlPolicy]:
        policies = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find all comm control policies in organization {org_name}")
        policies_fields = rest_client.comm_control.get_policies()
        for policy_fields in policies_fields:
            policy = CommControlPolicy(rest_client=rest_client, initial_data=policy_fields)
            policies.append(policy)
        if len(policies):
            logger.debug(f"Found these comm control policies: \n {policies}")
            return policies
        assert safe, f"Didn't find comm control policies in organization {self._organization_name}"
        logger.info(f"Didn't find comm control policies in organization {self._organization_name}")
        return policies

