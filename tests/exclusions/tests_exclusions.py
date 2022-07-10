
import allure
import pytest


from abc import abstractmethod


@allure.epic("Management")
@allure.feature("exclusions")
@pytest.mark.sanity
@pytest.mark.management_sanity
class ExclusionsTests:


    @pytest.mark.xray('')
    def test_verify_file_is_excluded(self, management,collector):
            """
            1.Login
            2.Go to security settings - Exclusion Manager
            3.Add list
            4.Rename list
            5.Add exclusion file
            8.Delete file
            9.delete list
            10.Logout
            """

            rest_collector = management.tenant.rest_components.collectors.get_by_ip(ip=collector.host_ip)
            test_im_params = {
                "eventName": "DynamicCodeTests.exe",
                "collectorName": rest_collector.get_name(from_cache=True)
            }
            management.ui_client.exclusion.add_new_exclusion_file(test_im_params)




    @abstractmethod
    def test_trigger_exclusion(self, collector):
        """
        1.Running the Excluded file from collector side
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





    @pytest.mark.xray('')
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

























    












