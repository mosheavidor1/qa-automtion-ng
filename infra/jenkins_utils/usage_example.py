import third_party_details
from infra.jenkins_utils.jenkins_handler import JenkinsHandler

jenkins_handler = JenkinsHandler(user_name=third_party_details.USER_NAME,
                                 password=third_party_details.JENKINS_API_TOKEN,
                                 jenkins_url=third_party_details.JENKINS_URL)

jenkins_handler.connect_to_jenkins_server()

job_params = {
    'content_branch': 'master',
    'ensilomgmt_branch': 'release/golf-p1',
    'ENSILO_VERSION': '4.1.0',
    'brandName': 'FortiEDR',
    'min_core_version': '',
    'min_management_version': '',
    'WINDOWS_COLLECTOR_VERSION': '',
    'OSX_COLLECTOR_VERSION': '4.1.0.132',
    'CENTOS6_COLLECTOR_VERSION': '',
    'CENTOS7_COLLECTOR_VERSION': '',
    'CENTOS8_COLLECTOR_VERSION': '',
    'ORACLE7_COLLECTOR_VERSION': '',
    'ORACLE8_COLLECTOR_VERSION': '',
    'Ubuntu1604_COLLECTOR_VERSION': '',
    'Ubuntu1804_COLLECTOR_VERSION': '',
    'Ubuntu2004_COLLECTOR_VERSION': '',
    'AmazonLinux_COLLECTOR_VERSION': '',
    'SLES15_COLLECTOR_VERSION': '',
    'SLES12_COLLECTOR_VERSION': '',
}

build = jenkins_handler.start_job(job_name='Content_Build_Collector_only', job_params=job_params)

state = jenkins_handler.wait_for_build_concrete_state(build=build, timeout=10 * 60, sleep_interval=30)

if state != 'SUCCESS':
    print("Job failed")

build_number = build.buildno
print(build_number)
