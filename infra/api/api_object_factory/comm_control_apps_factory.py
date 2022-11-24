from infra.api.api_object_factory.base_api_obj import BaseApiObjFactory
from infra.api.management_api.base_comm_control_app import BaseCommControlApp
from infra.api.management_api.comm_control_app_versions_cluster import CommControlAppVersionsCluster, ApplicationFieldsNames
from infra.api.management_api.comm_control_app import CommControlApp
from infra.api.nslo_wrapper.rest_commands import RestCommands
import logging
from typing import List
logger = logging.getLogger(__name__)


class CommControlAppFactory(BaseApiObjFactory):
    """ Find Comm control applications and return them as rest objects  with the user's credentials.
    The factory's rest credentials will be set as the default auth of each of the returned
    application objects so these credentials should be the credentials of a tested user
    1. We have an CommControlApp obj that is actually aggregation of all the different installed version of this app and
     each action on this obj will affect all its different installed versions
    2. We have a CommControlAppVersion obj that represents obj for a specific installed version
    """

    def __init__(self, organization_name: str, factory_rest_client: RestCommands):
        super().__init__(factory_rest_client=factory_rest_client)
        self._organization_name = organization_name

    def get_app_installed_versions_cluster_by_name(self, app_name, rest_client=None, safe=False) -> CommControlAppVersionsCluster:
        """ Returning aggregations of all the different installed versions of this app, each action on this obj will
        affect all its different installed versions, cluster of versions does not have version attribute.
        """
        rest_client = rest_client or self._factory_rest_client
        field_name = ApplicationFieldsNames.PRODUCT.value
        apps = self.get_by_field(field_name=field_name, value=app_name, rest_client=rest_client, safe=safe)
        if not apps:
            return None
        versions_cluster = [app for app in apps if not hasattr(app, ApplicationFieldsNames.VERSION.value)]
        assert len(versions_cluster) == 1, "Bug!!- we have more than one obj that represents the cluster of the same " \
                                           "app"
        return versions_cluster[0]

    def get_app(self, app_name, version, rest_client=None, safe=False) -> CommControlApp:
        rest_client = rest_client or self._factory_rest_client
        field_name = ApplicationFieldsNames.PRODUCT.value
        apps = self.get_by_field(field_name=field_name, value=app_name, rest_client=rest_client, safe=safe)
        specific_app_version = [app for app in apps if hasattr(app, ApplicationFieldsNames.VERSION.value) and
                                app.version == version]
        if specific_app_version:
            assert len(specific_app_version) == 1, "Bug!!- we have more than one obj with same version"
            return specific_app_version[0]
        if safe:
            return None
        raise Exception(f"The app {app_name} in version '{version}' does not exists")

    def get_installed_app_versions(self, app_name, rest_client=None, safe=False) -> List[CommControlApp]:
        """ Return all the installed app's versions, obj for each version """
        rest_client = rest_client or self._factory_rest_client
        field_name = ApplicationFieldsNames.PRODUCT.value
        apps = self.get_by_field(field_name=field_name, value=app_name, rest_client=rest_client, safe=safe)
        apps = [app for app in apps if hasattr(app, ApplicationFieldsNames.VERSION.value)]
        return apps

    def get_by_field(self, field_name, value, rest_client=None, safe=False) -> List[BaseCommControlApp]:
        """ Find applications by field name<>value and return their rest api wrappers,
        with the given rest client or the factory's rest client (should be some user's credentials)
        1. get all apps
        2. if app version is empty so this is the representation of the cluster of the versions
         else representation a specific version
        """
        apps = []
        rest_client = rest_client or self._factory_rest_client
        org_name = self._organization_name
        logger.debug(f"Find applications with field {field_name} = {value} in organization {org_name}")
        apps_fields = rest_client.comm_control.get_applications()
        for app_fields in apps_fields:
            if app_fields[field_name] == value:
                if not app_fields[ApplicationFieldsNames.VERSION.value]:
                    app = CommControlAppVersionsCluster(rest_client=rest_client, initial_data=app_fields)
                else:
                    app = CommControlApp(rest_client=rest_client, initial_data=app_fields)
                apps.append(app)
        if len(apps):
            logger.debug(f"Found these applications with field {field_name}={value}: \n {apps}")
            return apps
        assert safe, f"Didn't find any application with field {field_name}={value} in organization" \
                     f" {self._organization_name}"
        logger.info(f"Didn't find any application with field {field_name}={value} in organization"
                    f" {self._organization_name}")
        return apps

