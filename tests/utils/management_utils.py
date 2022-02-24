import allure
from infra.system_components.collector import Collector
from infra.system_components.management import Management


class ManagementUtils:

    @staticmethod
    @allure.step("create excepted event and check if created")
    def create_excepted_event_and_check(management: Management, collector: Collector, malware_name):
        """
        create event with existing exception and check if created
        """
        management.rest_api_client.delete_all_events()
        collector.create_event(malware_name=malware_name)
        events = management.rest_api_client.get_security_events(validation_data={"process": malware_name},
                                                                timeout=10, fail_on_no_events=False)
        return True if len(events) > 0 else False

