import os
import subprocess
import pathlib
import json
from datetime import datetime

import allure

from infra.allure_report_handler.reporter import Reporter
from infra.assertion.assertion import AssertTypeEnum, Assertion
from infra.utils.utils import StringUtils


class TestImHandler:
    script_dir = pathlib.Path(__file__).parent.resolve()

    def __init__(self, branch="master", local=True, headless=True):
        self.branch = branch
        self.local = local
        self.headless = headless

    @allure.step("Invoke TestIm command to start test")
    def _send_command(self,
                      test_name: str,
                      build_number: str,
                      url: str,
                      json_name: str = "params-file.json",
                      assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                      test_timeout=600):

        params_file = '' if json_name is None else f'--params-file "{json_name}"'

        if self.local:

            if not self.headless:
                headless = ''
            else:
                headless = "--headless --mode selenium"

            testim_cmd = fr'testim --token "jlSw4kxFGDMLPHORAp9uGnAxSFVuY2NOqnpDQDc98ykPcC9JXP" --project ' \
                         fr'"IxC1N5cIf88Pa3ktjRmX"  --name "{test_name}" ' \
                         fr'--use-local-chrome-driver  {headless} ' \
                         fr'{params_file} --base-url  https://{url} ' \
                         fr'--branch "{self.branch}" --test-config "FHD 1920x1080" '

        else:
            testim_cmd = fr'testim --token "jlSw4kxFGDMLPHORAp9uGnAxSFVuY2NOqnpDQDc98ykPcC9JXP" --project ' \
                         fr'"IxC1N5cIf88Pa3ktjRmX" --grid "Testim-Grid" ' \
                         fr'--report-file test-results\testim-tests-{test_name}-{build_number}-report.xml --name "{test_name}" ' \
                         fr'{params_file} --base-url  https://{url}'

        output = None
        status_code = 0
        try:
            Reporter.report(f"Going to run TestIM command from the dir: {self.script_dir}")
            Reporter.attach_str_as_file(file_name="TestIM command", file_content=testim_cmd)
            output = subprocess.check_output(testim_cmd, cwd=self.script_dir, shell=True, timeout=test_timeout)
        except subprocess.CalledProcessError as grepexc:
            status_code = grepexc.returncode
            output = grepexc.output

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

    def _create_param_file(self, json_params_name: str, data: dict):

        json_params_name_curr_dir = os.path.join(self.script_dir, json_params_name)

        if data is not None:

            if os.path.isfile(json_params_name_curr_dir):
                os.remove(json_params_name_curr_dir)

            Reporter.report("Creating Params json file")
            content = json.dumps(data, indent=4)
            Reporter.attach_str_as_file(file_name=json_params_name_curr_dir, file_content=content)

            with open(json_params_name_curr_dir, "w") as file:
                file.write(content)

    @allure.step("Run TestIM ---{test_name}--- on {management_ui_ip} UI")
    def run_test(self,
                 test_name: str,
                 buildnumber: str,
                 management_ui_ip: str,
                 assert_type: AssertTypeEnum = AssertTypeEnum.HARD,
                 data: dict = None,
                 test_timeout=600):
        """
        test name: has to be equal to the test name in TESTIM
        """
        curr_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        json_name = f"params-file-{test_name}-{buildnumber}-{curr_time}.json".replace(" ", "_").replace("|", "")

        try:
            self._create_param_file(json_params_name=json_name, data=data)

            self._send_command(test_name=test_name,
                               build_number=buildnumber,
                               url=management_ui_ip,
                               json_name=json_name,
                               assert_type=assert_type,
                               test_timeout=test_timeout)
        finally:
            os.remove(os.path.join(self.script_dir, json_name))
