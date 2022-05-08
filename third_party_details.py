import os

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
USER_NAME_DOMAIN = f'ensilo\\{USER_NAME}'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_QA_PATH = fr'{SHARED_DRIVE_PATH}\qa'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'
SHARED_DRIVE_LINUX_VERSIONS_PATH = fr"{SHARED_DRIVE_VERSIONS_PATH}\linux-collector"

JENKINS_JOB = fr'{os.getenv("BUILD_URL")}allure/' if os.getenv("BUILD_URL") is not None else None

TEST_IM_HEADLESS = False
TEST_IM_ON_REMOTE_GRID = False
RUN_TEST_IM_ON_PROXY = True if os.getenv("use_test_im_proxy") == 'true' else False

ENVIRONMENT_SERVICE_URL = 'http://environment-service.ensilo.local'
AUTOMATION_SERVICES_UTILS_MACHINE_IP = '10.151.121.54' # workaround for now, in the future we will create proxy machine per run in jenkins
LATEST_VERSIONS_SERVICE_PORT = 5070
TEST_IM_PROXY_PORT = 5071
TEST_IM_BRANCH = os.getenv("testim_branch") if os.getenv("testim_branch") is not None else "master"

