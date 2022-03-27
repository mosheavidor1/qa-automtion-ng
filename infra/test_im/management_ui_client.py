import sut_details
import third_party_details
from infra.assertion.assertion import AssertTypeEnum
from infra.test_im.test_im_handler import TestImHandler


class ManagementUiClient:

    def __init__(self,
                 management_ui_ip=sut_details.management_host):
        self.management_ui_ip = management_ui_ip
        self._testim_handler = TestImHandler(branch=third_party_details.TEST_IM_BRANCH)

        self.generic_functionality = self.FortiEdrGenericFunctionality(self)
        self.exceptions = self.FortiEdrExceptions(self)
        self.security_events = self.FortiEdrSecurityEvents(self)
        self.security_policies = self.FortiEdrSecurityPolicies(self)
        self.audit = self.FortiEdrAudit(self)
        self.dynamic_content = self.FortiEdrDynamicContent(self)
        self.fcs = self.FortiEdrFCS(self)
        self.connectors = self.FortiEdrConnectors(self)
        self.inventory = self.FortiEdrInventory(self)
        self.collectors = self.FortiEdrCollectors(self)
        self.ip_set = self.FortiEdrIpSet(self)
        self.ldap = self.FortiEdrLDAP(self)
        self.organizations = self.FortiEdrOrganizations(self)
        self.system_events = self.FortiEdrSystemEvents(self)
        self.users = self.FortiEdrUsers(self)

    def start_testim_flow(self,
                          test_name: str,
                          management_ui_ip=sut_details.management_host,
                          data: dict = None,
                          assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                          test_timeout=600):
        base_data = {
            "loginUser": "admin",
            "loginPassword": "12345678",
            "loginOrganization": "",
            "organization": "Default",
            "collectorName": "collector1"
        }

        if data is not None:
            base_data.update(data)

        self._testim_handler.run_test(test_name=test_name,
                                      ui_ip=management_ui_ip,
                                      data=base_data,
                                      assert_type=assert_type,
                                      test_timeout=test_timeout)

    class FortiEdrGenericFunctionality:
        def __init__(self, parent):
            self.parent = parent

        def ui_navigation(self,
                          data: dict = None,
                          assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                          test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="UI | Navigation",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def ui_dashboard(self,
                         data: dict = None,
                         assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                         test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="UI | Dashboard",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrOrganizations:
        def __init__(self, parent):
            self.parent = parent

        def create_organization(self,
                                data: dict = None,
                                assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Organizations | create organization",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrExceptions:

        def __init__(self, parent):
            self.parent = parent

        def create_exception(self,
                             data: dict = None,
                             assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                             test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Exceptions | Create exception",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def delete_all_exceptions(self,
                                  data: dict = None,
                                  assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                  test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Exceptions | Delete all exception",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def edit_exceptions(self,
                            data: dict = None,
                            assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                            test_timeout: int = 600):
            if "groups" in data.keys():
                self.parent.start_testim_flow(test_name="Edit group",
                                              management_ui_ip=self.parent.management_ui_ip,
                                              data=data,
                                              assert_type=assert_type,
                                              test_timeout=test_timeout)
            if "destinations" in data.keys():
                self.parent.start_testim_flow(test_name="Edit destination",
                                              management_ui_ip=self.parent.management_ui_ip,
                                              data=data,
                                              assert_type=assert_type,
                                              test_timeout=test_timeout)
            if "users" in data.keys():
                self.parent.start_testim_flow(test_name="Edit user",
                                              management_ui_ip=self.parent.management_ui_ip,
                                              data=data,
                                              assert_type=assert_type,
                                              test_timeout=test_timeout)
            if "comment" in data.keys():
                self.parent.start_testim_flow(test_name="Edit comment",
                                              management_ui_ip=self.parent.management_ui_ip,
                                              data=data,
                                              assert_type=assert_type,
                                              test_timeout=test_timeout)

        def add_another_exception(self,
                                  data: dict = None,
                                  assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                  test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Add another exception",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrSecurityEvents:

        def __init__(self, parent):
            self.parent = parent

        def search_event(self,
                         data: dict = None,
                         assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                         test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | Search event",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def archive_all(self,
                        data: dict = None,
                        assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                        test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | Archive all",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def event_does_not_appear(self,
                                  data: dict = None,
                                  assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                  test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | Event does not appear",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def search_archived_event(self,
                                  data: dict = None,
                                  assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                  test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | Search Archived event",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def export_excel_report(self,
                                data: dict = None,
                                assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | export Excel report",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def export_pdf_report(self,
                              data: dict = None,
                              assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                              test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | export PDF report",
                                          management_management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def check_if_event_in_simulation_block_mode(self,
                                                    data: dict = None,
                                                    assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                                    test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security event | If event in SimulationBlock mode",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrAudit:

        def __init__(self, parent):
            self.parent = parent

        def export_report(self,
                          data: dict = None,
                          assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                          test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Audit | Export report",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrDynamicContent:
        def __init__(self, parent):
            self.parent = parent

        def add_exception(self,
                          data: dict = None,
                          assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                          test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Dynamic content | Add exception",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrFCS:
        def __init__(self, parent):
            self.parent = parent

        def validate_connection_to_fcs_by_vulnerability(self,
                                                        data: dict = None,
                                                        assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                                        test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="FCS | Validation connection to FCS by Vulnerability",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def validate_connection_to_fcs_by_reclassification(self,
                                                           data: dict = None,
                                                           assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                                           test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="FCS | Validation connection to FCS by Reclassification",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrConnectors:
        def __init__(self, parent):
            self.parent = parent

        def create_custom_connector(self,
                                    data: dict = None,
                                    assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                    test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="connectors | create custom connector",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def check_custom_connector_enforcement(self,
                                               data: dict = None,
                                               assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                               test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Connectors | Check custom connector enforcement",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrInventory:
        def __init__(self, parent):
            self.parent = parent

        def check_components_are_up(self,
                                    data: dict = None,
                                    assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                    test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Inventory | check components running",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def verify_collector_is_running(self,
                                        data: dict = None,
                                        assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                        test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Inventory | Verify Collector is Running",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def collector_group_deletion_test(self,
                                          data: dict = None,
                                          assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                          test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Inventory | Collector Group deletion tests",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def delete_group(self,
                         data: dict = None,
                         assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                         test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Collectors | Delete group",
                                      management_ui_ip=self.parent.management_ui_ip,
                                      data=data,
                                      assert_type=assert_type,
                                      test_timeout=test_timeout)

    class FortiEdrCollectors:
        def __init__(self, parent):
            self.parent = parent

        def export_pdf_report(self,
                              data: dict = None,
                              assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                              test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="collectors | export PDF report",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def export_excel_report(self,
                                data: dict = None,
                                assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="collectors | export EXCEL report",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def add_group(self,
                      data: dict = None,
                      assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                      test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Collectors | Add group",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def disabled_and_enabled_collector(self,
                                           data: dict = None,
                                           assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                           test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Collectors | disabled and enabled collector",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def move_between_organizations(self,
                                       data: dict = None,
                                       assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                       test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Collectors | Move between organization",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrIpSet:
        def __init__(self, parent):
            self.parent = parent

        def set_new_ip_set(self,
                           data: dict = None,
                           assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                           test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="IP Set | Set new IP set",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrLDAP:
        def __init__(self, parent):
            self.parent = parent

        def set_ldap_server_plus_users_authentication(self,
                                                      data: dict = None,
                                                      assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                                      test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="LDAP | Set LDAP server plus users authentication",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrSecurityPolicies:
        def __init__(self, parent):
            self.parent = parent

        def set_policies(self,
                         data: dict = None,
                         assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                         test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Security policies | Set policies",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrSystemEvents:
        def __init__(self, parent):
            self.parent = parent

        def export_pdf_report(self,
                              data: dict = None,
                              assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                              test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="System event | export PDF report",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

        def prevention_simulation(self,
                                  data: dict = None,
                                  assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                  test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="system events | prevention simulation",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)

    class FortiEdrUsers:
        def __init__(self, parent):
            self.parent = parent

        def create_4_local_users_all_combinations(self,
                                                 data: dict = None,
                                                 assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                                                 test_timeout: int = 600):
            self.parent.start_testim_flow(test_name="Users | Create 4 local user - all combinations",
                                          management_ui_ip=self.parent.management_ui_ip,
                                          data=data,
                                          assert_type=assert_type,
                                          test_timeout=test_timeout)
