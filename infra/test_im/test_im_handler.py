import os
import subprocess
import pathlib
import json
from datetime import datetime

import allure
import requests

import third_party_details
from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import AssertTypeEnum, Assertion
from infra.utils.utils import StringUtils


class TestImHandler:
    script_dir = pathlib.Path(__file__).parent.resolve()

    def __init__(self,
                 branch="master"):
        self.branch = branch

    def _get_testim_cmd(self,
                        test_name: str,
                        params_file_name: str,
                        ui_ip: str,
                        branch_name: str = 'main'):

        json_file_param = ''
        branch_name_param = ''
        headless_param = ''

        if params_file_name is not None and '.json' in params_file_name:
            json_file_param = f'--params-file "{params_file_name}"'

        if branch_name is not None:
            branch_name_param = fr'--branch "{branch_name}"'

        if third_party_details.TEST_IM_HEADLESS:
            headless_param = "--headless --mode selenium"

        testim_cmd = fr'testim --token "jlSw4kxFGDMLPHORAp9uGnAxSFVuY2NOqnpDQDc98ykPcC9JXP" ' \
                     fr'--project "IxC1N5cIf88Pa3ktjRmX"  --name "{test_name}" ' \
                     fr'{json_file_param} ' \
                     fr'--base-url  https://{ui_ip} '

        if third_party_details.TEST_IM_ON_REMOTE_GRID is True:
            testim_cmd += fr'--grid "Testim-Grid" ' \
                          fr'--report-file test-results\testim-tests-{test_name}-report.xml '

        else:
            testim_cmd += fr'--use-local-chrome-driver ' \
                          fr'{headless_param} ' \
                          fr'{branch_name_param} ' \
                          fr'--test-config "FHD 1920x1080" '

        return testim_cmd

    @allure.step("Run TestIM ---{test_name}--- on {ui_ip} UI")
    def run_test(self,
                 test_name: str,
                 ui_ip: str,
                 data: dict = None,
                 assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                 test_timeout=600):

        json_name = None

        if not third_party_details.RUN_TEST_IM_ON_PROXY:
            json_name = self._create_param_file(data=data)

        testim_cmd = self._get_testim_cmd(test_name=test_name,
                                          params_file_name=json_name,
                                          ui_ip=ui_ip,
                                          branch_name=self.branch)

        Reporter.attach_str_as_file(file_name="TestIM command", file_content=testim_cmd)

        output = None
        status_code = 0

        if third_party_details.RUN_TEST_IM_ON_PROXY is True:
            status_code, output = self._send_commands_via_test_im_proxy(testim_cmd=testim_cmd,
                                                                        data=data,
                                                                        test_timeout=test_timeout)
        else:
            try:
                Reporter.report(f"Going to run TestIM command from the dir: {self.script_dir}")
                output = subprocess.check_output(testim_cmd, cwd=self.script_dir, shell=True, timeout=test_timeout)

            except subprocess.CalledProcessError as grepexc:
                status_code = grepexc.returncode
                output = grepexc.output

            finally:
                if json_name is not None:
                    os.remove(os.path.join(self.script_dir, json_name))

        if isinstance(output, bytes):
            output = output.decode('utf-8')

        Reporter.attach_str_as_file(file_name=f'TestIm output', file_content=output)

        test_link_regex = r'Test\s+.+url:\s+(.+)\n'
        test_link = StringUtils.get_txt_by_regex(text=output, regex=test_link_regex, group=1)
        passed = StringUtils.get_txt_by_regex(text=output, regex='PASSED:\s+(\d+)', group=1)
        failed = StringUtils.get_txt_by_regex(text=output, regex='FAILED:\s+(\d+)', group=1)
        evaluating = StringUtils.get_txt_by_regex(text=output, regex='EVALUATING:\s+(\d+)', group=1)
        aborted = StringUtils.get_txt_by_regex(text=output, regex='ABORTED:\s+(\d+)', group=1)
        skipped = StringUtils.get_txt_by_regex(text=output, regex='SKIPPED:\s+(\d+)', group=1)
        duration = StringUtils.get_txt_by_regex(text=output, regex='Duration:\s+(\S+)', group=1)

        if output is None or passed is None or failed is None:
            assert False, "Failed to run test or output is empty, something is wrong"

        Reporter.report(f"Test link: {test_link}")
        Reporter.report(f"Test Duration: {duration}")

        if status_code != 0 and passed is not None and passed.isdigit():
            if int(passed) == 0:

                if assert_type == AssertTypeEnum.SOFT:
                    Assertion.add_message_soft_assert(message=f"The test step \ test from TestIM: {test_name} has failed")

                else:
                    assert False, f"Test Failed, look at TestIm link to see what happened: {test_link}"

        if int(failed) != 0:
            if assert_type == AssertTypeEnum.SOFT:
                Assertion.add_message_soft_assert(message=f"The test step \ test from TestIM: {test_name} has failed")
            else:
                assert False, f"Test Failed, look at TestIm link to see what happened: {test_link}"

    def _create_param_file(self, data: dict):

        curr_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        json_params_name = f"params-file-{curr_time}.json".replace(" ", "_").replace("|", "")

        json_params_name_curr_dir = os.path.join(self.script_dir, json_params_name)

        if os.path.isfile(json_params_name_curr_dir):
            os.remove(json_params_name_curr_dir)

        Reporter.report("Creating Params json file")
        content = json.dumps(data, indent=4)
        Reporter.attach_str_as_file(file_name=json_params_name_curr_dir, file_content=content)

        with open(json_params_name_curr_dir, "w") as file:
            file.write(content)

        file_name_to_return = json_params_name_curr_dir.replace(str(self.script_dir), '').replace('\\', ''.replace('/', ''))

        return file_name_to_return

    @allure.step("Run testIM through proxy windows machine")
    def _send_commands_via_test_im_proxy(self,
                                         testim_cmd: str,
                                         data: dict,
                                         test_timeout: int = 600):
        data = {
            'testim_cmd': testim_cmd,
            'params': data,
            'timeout': test_timeout
        }

        Reporter.report("Going to start TEST IM - through proxy windows machine")
        url = f'http://{third_party_details.TEST_IM_PROXY_IP}:{third_party_details.TEST_IM_PROXY_PORT}/startTestim'
        Reporter.attach_str_as_file(file_name=url, file_content=json.dumps(data, indent=4))

        response = requests.post(url=url, json=data, timeout=test_timeout)
        assert response.status_code == 200, f"Proxy Machine returned {response.status_code} , failed to proccess the request and run the test"
        resp_as_dict = json.loads(response.content)
        test_im_cmd_status_code = resp_as_dict.get('status_code')
        test_im_cmd_output = resp_as_dict.get('output')
        return test_im_cmd_status_code, test_im_cmd_output


