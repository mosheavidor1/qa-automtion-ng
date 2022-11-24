import os
import subprocess
import pathlib
import json
from datetime import datetime


class TestImProxy:
    script_dir = pathlib.Path(__file__).parent.resolve()

    @staticmethod
    def run_test(test_im_cmd: str,
                 data: dict = None,
                 test_timeout=600):

        json_name = None
        if data is not None and data != {}:
            json_name = TestImProxy.create_param_file(data=data)
            test_im_cmd = f'{test_im_cmd} --params-file "{json_name}"'

        output = None
        status_code = 0

        try:
            output = subprocess.check_output(test_im_cmd, cwd=TestImProxy.script_dir, shell=True, timeout=test_timeout)

        except subprocess.CalledProcessError as grepexc:
            status_code = grepexc.returncode
            output = grepexc.output

        finally:
            if json_name is not None:
                os.remove(os.path.join(TestImProxy.script_dir, json_name))

        if isinstance(output, bytes):
            output = output.decode('utf-8')

        return status_code, output

    @staticmethod
    def create_param_file(data: dict):

        curr_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        json_params_name = f"params-file-{curr_time}.json".replace(" ", "_").replace("|", "")

        json_params_name_curr_dir = os.path.join(TestImProxy.script_dir, json_params_name)

        if data is not None:

            if os.path.isfile(json_params_name_curr_dir):
                os.remove(json_params_name_curr_dir)

            print("Creating Params json file")
            content = json.dumps(data, indent=4)

            with open(json_params_name_curr_dir, "w") as file:
                file.write(content)

        file_name_to_return = json_params_name_curr_dir.replace(str(TestImProxy.script_dir), '').replace('\\', ''.replace('/', ''))

        return file_name_to_return
