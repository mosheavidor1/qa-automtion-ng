#!/bin/bash


env
ln -s /home/pip_lib/.local .local

pip install ensilo-platform-rest@git+ssh://git@dops-git106.fortinet-us.com/ecs/ensilo-platform-rest.git@master


export PATH=$PATH:./.local/bin

pytest -v -m "${suite_name}" --alluredir="./allure-results" --jira-xray