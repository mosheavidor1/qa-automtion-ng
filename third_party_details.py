import os

USER_NAME = 'automation'
PASSWORD = 'Aut0g00dqa42'
SHARED_DRIVE_PATH = r'\\ens-fs01.ensilo.local'
SHARED_DRIVE_VERSIONS_PATH = fr'{SHARED_DRIVE_PATH}\Versions'
JENKINS_JOB = os.getenv("BUILD_URL") if os.getenv("BUILD_URL") is not None else None

