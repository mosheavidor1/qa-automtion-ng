import os

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
USER_NAME_DOMAIN = f'ensilo\\{USER_NAME}'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_QA_PATH = fr'{SHARED_DRIVE_PATH}\qa'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'

JENKINS_JOB = fr'{os.getenv("BUILD_URL")}allure/' if os.getenv("BUILD_URL") is not None else None

TEST_IM_HEADLESS = False
TEST_IM_ON_REMOTE_GRID = False
RUN_TEST_IM_ON_PROXY = True if os.getenv("use_test_im_proxy") == 'true' else False
TEST_IM_PROXY_IP = '10.151.120.162' # workaround for now, in the future we will create proxy machine per run in jenkins
TEST_IM_PROXY_PORT = 5060
TEST_IM_BRANCH = os.getenv("testim_branch") if os.getenv("testim_branch") is not None else "master"

