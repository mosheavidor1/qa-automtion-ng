import allure
import pytest
import time


from abc import abstractmethod

from tests.EDR.conftest import EDR_EVENT_TESTER_REGISTRATION_PASSWORD


@allure.epic("Management")
@allure.feature("exclusions")
@pytest.mark.sanity
@pytest.mark.management_sanity
class ExclusionsTests:

    @pytest.mark.xray('EN-76121')
    def test_Create_New_Excluded_File(self, management, collector):
        """
            1.Login.
            2.Go to security settings - Exclusion Manager.
            3.Create new list.
            4.Choose collector group.
            5.Create new Process Exclusion File.
            6.Close the browser.
            """

        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.exclusion.add_new_exclusion_file(test_im_params)
        time.sleep(200)

    @abstractmethod
    def test_trigger_exclusion(self, collector):
        """
        1.Trigger the Excluded file from collector side
        """
        event_name = "DynamicCodeTests.exe"
        collector.create_event(malware_name=event_name)

    @pytest.mark.xray('')
    def test_file_is_excluded_check(self, management, collector):
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.file_excluded_check.test_file_is_excluded_check(test_im_params)

    @pytest.mark.xray('EN-71219')
    def test_delete_exclusions(self, management, collector):
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.remove_exclusion.delete_exclusions(test_im_params)
        event_name = "DynamicCodeTests.exe"
        collector.create_event(malware_name=event_name)

    @pytest.mark.xray('')
    def test_file_not_excluded_check(self, management, collector):
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.file_not_excluded_check.test_file_not_excluded_check(test_im_params)

    @pytest.mark.xray('')
    def test_delete_security_events(self, management, collector):
        rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
        test_im_params = {
            "eventName": "DynamicCodeTests.exe",
            "collectorName": rest_collector.get_name(from_cache=True)
        }
        management.ui_client.remove_security_events.delete_security_events(test_im_params)

    @pytest.mark.xray('')
    def test_delete_events(self, management):
        user = management.tenant.default_local_admin

        user.rest_components.events.delete_all(safe=True)

    @pytest.mark.xray('')
    def test_stop_collector(self, collector):
        collector_agent = collector

        collector_agent.stop_collector(password=EDR_EVENT_TESTER_REGISTRATION_PASSWORD)



    @abstractmethod
    def test_reboot(self, collector):

        collector.reboot
