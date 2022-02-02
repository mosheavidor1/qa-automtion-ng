import os

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
USER_NAME_DOMAIN = f'ensilo\\{USER_NAME}'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_QA_PATH = fr'{SHARED_DRIVE_PATH}\qa'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'
JENKINS_JOB = fr'{os.getenv("BUILD_URL")}allure/' if os.getenv("BUILD_URL") is not None else None
