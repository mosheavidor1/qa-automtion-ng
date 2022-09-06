import sut_details
from infra.api.nslo_wrapper.rest_commands import RestCommands


class _AdminRestCreator:
    def __init__(self):
        self._admin_rest: RestCommands | None = None

    def __call__(self, *_, **__):
        if self._admin_rest is None or self._admin_rest.is_management_ip_changed(sut_details.management_host):
            self._admin_rest = RestCommands(
                sut_details.management_host,
                sut_details.rest_api_user,
                sut_details.rest_api_user_password,
            )
        return self._admin_rest


ADMIN_REST = _AdminRestCreator()
