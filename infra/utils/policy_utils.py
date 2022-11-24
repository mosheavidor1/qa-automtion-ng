from infra.api.management_api.security_policy import SecurityPolicy
import logging
from typing import List
from infra.api.management_api.security_policy import DefaultPoliciesNames
from infra.api.api_object_factory.security_policies_factory import SecurityPoliciesFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
logger = logging.getLogger(__name__)


def get_default_policies(rest_client: RestCommands, organization_name) -> List[SecurityPolicy]:
    """ Return the default policies --> the most popular policies """
    policies_factory: SecurityPoliciesFactory = SecurityPoliciesFactory(organization_name=organization_name,
                                                                        factory_rest_client=rest_client)
    policies = []
    for policy_name in DefaultPoliciesNames:
        policy = policies_factory.get_by_name(policy_name=policy_name.value)
        policies.append(policy)
    return policies
