import pytest


@pytest.fixture(scope='function')
def fx_system_without_ldap_auth(management):
    """
    This fixture making sure that the system is clear from configuration of LDAP before the test
    And make cleanup after the  test
    """
    management.ui_client.ldap.reset_ldap_server_configuration()
    yield management
    management.ui_client.ldap.reset_ldap_server_configuration()
