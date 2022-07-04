import time

import urllib3
from jenkinsapi.build import Build
from jenkinsapi.jenkins import Jenkins


class JenkinsHandler:

    def __init__(self,
                 user_name,
                 password,
                 jenkins_url): # full url with port
        self.user_name = user_name
        self.password = password
        self.jenkins_url = jenkins_url
        self.__jenkins_server_connection = None

        self.__disable_warnings()

    def __disable_warnings(self):
        urllib3.disable_warnings(urllib3.exceptions.MaxRetryError)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def connect_to_jenkins_server(self, force: bool = False):
        if self.__jenkins_server_connection or force is True:
            self.__jenkins_server_connection = Jenkins(self.jenkins_url,
                                                       username=self.user_name,
                                                       password=self.password,
                                                       ssl_verify=False)

    def get_jenkins_job(self, job_name: str):
        num_reries = 10
        count = 1

        while count <= num_reries:
            try:
                jenkins_job = self.__jenkins_server_connection.get_job(job_name)
                return jenkins_job
            except Exception:
                count += 1
                time.sleep(5)

        raise Exception('Failed get the job')

    def start_job(self, job_name: str, job_params: dict):
        job = self.get_jenkins_job(job_name=job_name)
        last_build_number = job.get_last_buildnumber()
        triggered_build_number = last_build_number + 1
        run_started = False

        while not run_started:
            try:
                self.__jenkins_server_connection.build_job(job_name, job_params)
                run_started = True
            except ValueError as value_err:
                if 'Not a Queue URL:' not in value_err.__str__():
                    raise value_err

            time.sleep(15)
            triggered_build = self.get_build(job, triggered_build_number)
            return triggered_build

    def get_build(self, job, build_number: int) -> Build:
        get_build_retru_num = 10
        curr_try = 0

        while curr_try < get_build_retru_num:
            try:
                build = job.get_build(build_number)
                return build

            except Exception as e:
                print(e)
                time.sleep(6)

        raise Exception("Failed to get the job")

    def get_build_state(self, build: Build):

        num_retry = 15
        curr_try = 0

        while curr_try < num_retry:

            try:
                status = build.get_status()
                return status
            except:
                curr_try += 1
                time.sleep(60)

    def wait_for_build_concrete_state(self,
                                      build: Build,
                                      timeout=64800,
                                      sleep_interval=60):
        """
        Can be FAILURE, SUCCESS or None
        :return:
        """

        curr_time = time.time()
        build_concrete_state = None
        while time.time() - curr_time < timeout and build_concrete_state is None:
            build = self.get_build(job=build.job, build_number=build.buildno)
            build_concrete_state = self.get_build_state(build=build)
            if build_concrete_state is None:
                time.sleep(sleep_interval)

        assert build_concrete_state is not 'None', f"Failed to get build concrete state within timeout of {timeout}, seems like the job did not finished"

        return build_concrete_state