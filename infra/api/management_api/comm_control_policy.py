from infra.api.nslo_wrapper.rest_commands import RestCommands
from infra.api.management_api.base_policy import BasePolicy


class CommControlPolicy(BasePolicy):
    """ A wrapper of our internal rest client for working with communication control policy.
        Each policy will have its own rest credentials based on user password and name """

    def __init__(self, rest_client: RestCommands, initial_data: dict):
        super().__init__(rest_client=rest_client, initial_data=initial_data,
                         policy_rest=rest_client.communication_control)

    def __repr__(self):
        return f"Communication control Policy {self.name} in '{self.get_organization_name(from_cache=True)}'"





