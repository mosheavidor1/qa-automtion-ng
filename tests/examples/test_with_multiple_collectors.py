import logging

from infra.allure_report_handler.reporter import Reporter, TEST_STEP
from infra.enums import CollectorTypes
from infra.system_components.aggregator import Aggregator
from infra.system_components.collector import CollectorAgent
from infra.system_components.management import Management
from tests.utils.environment_utils import add_collectors_from_pool
logger = logging.getLogger(__name__)


def test_add_collectors_during_test(management: Management,
                                    aggregator: Aggregator,
                                    collector: CollectorAgent):
    desired_version = collector.get_version()

    desired_collectors = {
        CollectorTypes.WINDOWS_11_64: 2,
        CollectorTypes.WINDOWS_10_64: 2
    }

    with TEST_STEP('Add collectors to pool'):
        with add_collectors_from_pool(management=management,
                                      tenant=management.tenant,
                                      desired_version=desired_version,
                                      aggregator_ip=aggregator.host_ip,
                                      organization=management.tenant.organization.get_name(),
                                      registration_password=management.tenant.organization.registration_password,
                                      desired_collectors_dict=desired_collectors) as dynamic_collectors:
            for single_dynamic_collector in dynamic_collectors:
                Reporter.report(f"collector host ip: {single_dynamic_collector.host_ip}", logger_func=logger.info)
