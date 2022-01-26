#!/bin/bash


env
ln -s /home/pip_lib/.local .local

pip install ensilo-platform-rest@git+ssh://git@dops-git106.fortinet-us.com/ecs/ensilo-platform-rest.git@master


export PATH=$PATH:./.local/bin


# pytest -v -m "${tests}" --alluredir="./allure-results" --jira-xray

pytest_cmd="pytest -v "

if [ "$tests_discover_type" = "suite" ]; then
    pytest_cmd="${pytest_cmd} -m "
else
    pytest_cmd="${pytest_cmd} -k "
fi

pytest_cmd="${pytest_cmd} \"$tests\" --alluredir=\"./allure-results\" "

if [ "$report_results_to_jira" = "true" ]; then
     pytest_cmd="${pytest_cmd} --jira-xray"
fi

echo $pytest_cmd
eval $pytest_cmd


