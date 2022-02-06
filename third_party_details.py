import os

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
USER_NAME_DOMAIN = f'ensilo\\{USER_NAME}'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_QA_PATH = fr'{SHARED_DRIVE_PATH}\qa'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'
JENKINS_JOB = fr'{os.getenv("BUILD_URL")}allure/' if os.getenv("BUILD_URL") is not None else None

TEST_IM_PROXY_IP = '10.151.120.162'
TEST_IM_PROXY_PORT = 5055
RUN_TEST_IM_ON_PROXY = True if os.getenv("use_test_im_proxy") == 'true' else False

