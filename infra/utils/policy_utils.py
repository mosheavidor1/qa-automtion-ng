from infra.api.management_api.policy import Policy
import logging
from typing import List
from infra.api.management_api.policy import DefaultPoliciesNames
from infra.api.api_object_factory.policies_factory import PoliciesFactory
from infra.api.nslo_wrapper.rest_commands import RestCommands
logger = logging.getLogger(__name__)


def get_default_policies(rest_client: RestCommands, organization_name) -> List[Policy]:
    """ Return the default policies --> the most popular policies """
    policies_factory: PoliciesFactory = PoliciesFactory(organization_name=organization_name,
                                                        factory_rest_client=rest_client)
    policies = []
    for policy_name in DefaultPoliciesNames:
        policy = policies_factory.get_by_name(policy_name=policy_name.value)
        policies.append(policy)
    return policies
