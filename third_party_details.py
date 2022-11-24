import os
import random

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
JENKINS_API_TOKEN = '11207ededd75f01f6880eba42ab16bcf09'
JENKINS_URL = 'http://jenkins.ensilo.local/'
USER_NAME_DOMAIN = f'ensilo\\{USER_NAME}'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_QA_PATH = fr'{SHARED_DRIVE_PATH}\qa'
SHARED_DRIVE_LICENSE_PATH = fr'{SHARED_DRIVE_QA_PATH}\LicenseTool'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'
SHARED_DRIVE_COLLECTORS_CONTENT = fr"{SHARED_DRIVE_VERSIONS_PATH}\Collector_Content"
SHARED_DRIVE_LINUX_VERSIONS_PATH = fr"{SHARED_DRIVE_VERSIONS_PATH}\linux-collector"

JENKINS_JOB = fr'{os.getenv("BUILD_URL")}allure/' if os.getenv("BUILD_URL") is not None else None

TEST_IM_HEADLESS = False
TEST_IM_ON_REMOTE_GRID = False
RUN_TEST_IM_ON_PROXY = os.getenv("use_test_im_proxy") == 'true'

ENVIRONMENT_SERVICE_URL = 'http://environment-service.ensilo.local'
# workaround for now, in the future we will create proxy machine per run in jenkins
AUTOMATION_SERVICES_UTILS_MACHINE_IP = random.choice(['10.151.121.54', '10.151.120.164', '10.151.120.221',
                                                      '10.151.120.217'])
LATEST_VERSIONS_SERVICE_PORT = 5070
AUTOMATION_SERVICES_URL = f'http://{AUTOMATION_SERVICES_UTILS_MACHINE_IP}:{LATEST_VERSIONS_SERVICE_PORT}'
TEST_IM_PROXY_PORT = 5071
TEST_IM_BRANCH = os.getenv("testim_branch", default="master")
