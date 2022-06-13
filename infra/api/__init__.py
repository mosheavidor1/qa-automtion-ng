import sut_details
from infra.api.nslo_wrapper.rest_commands import RestCommands

ADMIN_REST = RestCommands(sut_details.management_host, sut_details.management_ui_admin_user_name,
                          sut_details.management_ui_admin_password)
