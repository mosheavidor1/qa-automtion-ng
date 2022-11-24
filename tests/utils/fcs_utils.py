import logging
from infra.system_components.management import Management
from infra.jenkins_utils.jenkins_handler import JenkinsHandler
from infra.enums import JenkinsJobStates
logger = logging.getLogger(__name__)

FCS_JOB_NAME = "QA_Upload_License_To_ECS"
FCS_JOB_TIMEOUT = 5 * 60
FCS_JOB_INTERVAL = 10


def register_management_to_fcs(management: Management):
    """
    Register management to fcs staging. See instructions here:
    http://confluence.ensilo.local/pages/viewpage.action?spaceKey=QA&title=How+to+connect+OnPrem+environment+to+FCS
    """
    logger.info(f"Register {management} to staging FCS")
    assert management.is_disconnected_from_fcs(), \
        f"{management} is not disconnected from FCS, status is: {management.get_fcs_status()}"
    management.add_fcs_staging_url_to_properties_file()
    jenkins_wrapper = JenkinsHandler()
    jenkins_wrapper.connect_to_jenkins_server()
    job_params = _generate_params_for_fcs_job(management=management)
    logger.info(f"Trigger jenkins fcs job {FCS_JOB_NAME} with params: {job_params}")
    build = jenkins_wrapper.start_job(job_name=FCS_JOB_NAME, job_params=job_params)
    build_number = build.buildno
    logger.info(f"Build number is :{build_number}")
    state = jenkins_wrapper.wait_for_build_concrete_state(build=build, timeout=FCS_JOB_TIMEOUT,
                                                          sleep_interval=FCS_JOB_INTERVAL)
    assert state == JenkinsJobStates.SUCCESS.value, \
        f"Job {FCS_JOB_NAME} with build {build_number} Failed, got state: {state}"

    management.wait_until_fcs_connected()


def _generate_params_for_fcs_job(management: Management):
    installation_id = management.details.installation_id
    customer_name = management.details.customer_name
    license_blob = management.get_license_blob()

    fcs_job_params = {
        "Customer": customer_name,
        "EnvironmentType": "staging",
        "RestUser": "enSiloCloudServices",
        "LicenseBlob": license_blob,
        "InstallationId": str(installation_id),
        "CloudProvider": 'OnPremise',
        "CloudProject": 'qa-production'
    }
    return fcs_job_params
