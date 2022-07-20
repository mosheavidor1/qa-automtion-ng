import allure
import pytest

from infra.allure_report_handler.reporter import TEST_STEP
from tests.utils.ldap_utils import get_base_ad_server_ldap_configuration, get_login_details_of_ad_ldap_non_admin_user, \
    get_login_details_of_ad_ldap_local_admin


@allure.epic("Management")
@allure.feature("LDAP")
@pytest.mark.sanity
@pytest.mark.ldap_sanity
@pytest.mark.management_sanity
@pytest.mark.xray('EN-73331')
def test_configure_ad_ldap_with_user_local_admin(fx_system_without_ldap_auth):
    """
    This test cofigure an existing active directory LDAP server with local admin user via management ui (exist a bug EN-77586)
    steps:
    1. set the LDAP
    2. Validate the connection by the test button
    3. validate the connection by preform login with ldap user (non admin user)
    4.  validate the connection by preform login with ldap local admin user
    """
    management = fx_system_without_ldap_auth
    test_im_params = get_base_ad_server_ldap_configuration()

    with TEST_STEP(f"Configure AD server LDAP {test_im_params['LDAP_host']} with local admin"):
        management.ui_client.ldap.set_ldap_server(test_im_params)

    ad_ldap_user_params = get_login_details_of_ad_ldap_non_admin_user()
    with TEST_STEP(
            f"Validation login with AD ldap user {ad_ldap_user_params['loginUser']} with user privileges of non admin user"):
        management.ui_client.ldap.validate_ldap_non_admin_user_privileges(ad_ldap_user_params)

    ad_ldap_local_admin_params = get_login_details_of_ad_ldap_local_admin()
    with TEST_STEP(
            f"Validation login with AD ldap local admin user {ad_ldap_local_admin_params['loginUser']} with user privileges"):
        management.ui_client.ldap.validate_ldap_local_admin_privileges(ad_ldap_local_admin_params)
