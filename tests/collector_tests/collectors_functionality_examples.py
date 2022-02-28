import allure
import pytest

from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import AssertTypeEnum
from tests.collector_tests.collectors_functionality_base import CollectorsTestsBase, \
    CollectorFunctionalityTestType


@allure.story("Collectors")
@allure.feature("Collectors Functionality")
# @pytest.mark.full_regression_example
# @pytest.mark.collectors_functionality_example
# @pytest.mark.fake_sanity
class CollectorFunctionalityExamples(CollectorsTestsBase):

    @pytest.mark.xray('EN-45431')
    def test_stop_collector_check_is_up_and_running_fail_on_purpose(self, management):
        """
        This test is going to fail on purpose
        Test steps:
        1. stop collector
        2. check if it's up and running
        """
        self.management = management
        self.test_type = CollectorFunctionalityTestType.STOP_COLLECTOR_CHECK_IS_UP_FAIL_ON_PURPOSE
        self.play_test()

    @pytest.mark.xray('EN-45432')
    def test_that_create_a_fake_dumps_file(self, management):
        """
        This test is going to fail on purpose
        Test steps:
        1. create fake dump file
        """
        self.management = management
        self.test_type = CollectorFunctionalityTestType.CREATE_FAKE_DUMP_FILE
        self.play_test()

    @pytest.mark.xray('EN-68879')
    def test_with_soft_assert(self, management):
        """
        The role of this test is to check stop and start of fortiEDR collector service
        Test steps:
        1. stop collector
        2. generate some kind soft assert
        3. check status
        """
        self.management = management
        self.collector = self.management.collectors[0]
        self.test_type = CollectorFunctionalityTestType.TEST_WITH_SOFT_ASSERT
        self.play_test()

    # @pytest.mark.test_im_example
    @pytest.mark.xray('EN-68892')
    def test_im_example(self, management):
        test_name = "Organizations | create organization"
        params = {"OrganizationName": "Org3"}
        self.testim_handler.run_test(test_name=test_name,
                                     ui_ip=management.host_ip,
                                     data=params,
                                     assert_type=AssertTypeEnum.HARD)
        Reporter.report("Just a print")
