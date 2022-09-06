# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import json
import os

from flask import Flask, request

# Flask constructor takes the name of
# current module (__name__) as argument.
from component_type_enum import ComponentTypeEnum

app = Flask(__name__)


def update_dict_only_if_key_does_not_exist(dictionary: dict, key, value):
    if key not in dictionary.keys():
        dictionary[key] = value


def append_value_to_list_if_dict_value_is_list(dictionary: dict, key, value, max_list_size: int = 1):
    if key not in dictionary.keys():
        dictionary[key] = [value]

    else:
        tmp_list = dictionary.get(key)
        if len(tmp_list) < max_list_size:
            tmp_list.append(value)


def filter_versions_above_build(build_threshold, versions_list):
    to_remove = []
    for i in range(len(versions_list)):
        curr_build = versions_list[i].split('.')[-1]
        if int(curr_build) > int(build_threshold):
            to_remove.append(versions_list[i])

    filtered = list(set(versions_list) - set(to_remove))
    return filtered


def get_latest_versions_according_to_versions_path_as_dict(versions_path: str,
                                                           base_version: str,
                                                           component_type: ComponentTypeEnum,
                                                           ignore_versions_above_threshold: int = None,
                                                           num_build_to_return_per_component: int = 1):
    all_dirs_in_version = os.listdir(versions_path)
    filtered_dirs = [x for x in all_dirs_in_version if base_version in x]

    if ignore_versions_above_threshold is not None:
        filtered_dirs = filter_versions_above_build(build_threshold=ignore_versions_above_threshold,
                                                    versions_list=filtered_dirs)

    if len(filtered_dirs) == 0:
        return {}

    sorted_filtered_dirs = sorted(filtered_dirs, key=lambda x: [int(i) if i.isdigit() else i for i in x.split('.')])
    sorted_filtered_dirs.reverse()
    print(sorted_filtered_dirs)

    all_versions_dict = {}
    for version in sorted_filtered_dirs:
        version_content_path = fr'{versions_path}\{version}'

        files_in_dir = os.listdir(version_content_path)
        if versions_path == r'X:':

            if f'FortiEDR_{version}.iso' in files_in_dir:
                if component_type == ComponentTypeEnum.MANAGER:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='management',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if component_type == ComponentTypeEnum.AGGREGATOR:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='aggregator',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if component_type == ComponentTypeEnum.CORE:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='core',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

            if component_type == ComponentTypeEnum.WINDOWS_COLLECTOR:
                if f'FortiEDRCollectorInstaller32_{version}.msi' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='windows_32_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller64_{version}.msi' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='windows_64_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

        elif versions_path == r'X:\linux-collector':
            if component_type == ComponentTypeEnum.LINUX_COLLECTOR:
                if f'FortiEDRCollectorInstaller_amazonlinux-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='amazonlinux',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_CentOS6-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='centos_6_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_CentOS7-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='centos_7_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_CentOS8-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='centos_8_collector',
                                                               value=version)

                if f'FortiEDRCollectorInstaller_openSUSE-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='openSUSE_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_Oracle7-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='oracle_7_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_Oracle8-{version}.x86_64.rpm' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='oracle_8_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_Ubuntu16.04-{version}.deb' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='ubuntu_16_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_Ubuntu18.04-{version}.deb' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='ubuntu_18_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

                if f'FortiEDRCollectorInstaller_Ubuntu20.04-{version}.deb' in files_in_dir:
                    append_value_to_list_if_dict_value_is_list(dictionary=all_versions_dict, key='ubuntu_20_collector',
                                                               value=version,
                                                               max_list_size=num_build_to_return_per_component)

    return all_versions_dict


@app.route('/list_content', methods=['GET'])
def list_content():
    num_last_content_files = int(request.args.get('num_last_content_files'))
    all_dirs_in_version = os.listdir(r'X:\Collector_Content')
    filtered_nslo = [x for x in all_dirs_in_version if 'FortiEDRCollectorContent' in x and 'nslo' in x and 'tmp' not in x]
    # filtered_json = [x for x in all_dirs_in_version if 'FortiEDRCollectorContent' in x and 'json' in x and 'tmp' not in x]

    filtered_nslo.sort(key=lambda o: int(o.split('FortiEDRCollectorContent-')[1].split('.nslo')[0]))
    filtered_nslo.reverse()

    # filtered_json.sort(key=lambda o: int(o.split('FortiEDRCollectorContent-')[1].split('.json')[0]))
    # filtered_json.reverse()

    response = app.response_class(
        response=json.dumps(filtered_nslo[:num_last_content_files]),
        status=200,
        mimetype='application/json'
    )
    return response


# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
@app.route('/latest_build', methods=['GET'])
def latest_build():
    base_version = request.args.get('base_version')
    num_builds = int(request.args.get('num_builds'))

    if base_version is None or base_version.count('.') != 2 or not os.path.exists('X:'):

        error_message = 'Invalid request'

        if base_version is None:
            error_message = 'can not extract latest version without passing base version as url param, ' \
                            'example: http://service_url/latest_build?base_version=5.2.0'

        elif base_version.count('.') != 2:
            error_message = 'invalid format for base version, use the following template 5.2.0 for example'

        elif not os.path.exists('X:'):
            error_message = r'\\ens-fs01.ensilo.local\Versions is not mounted on the server that the service running ' \
                            r'on, can not extract the versions'

        message = {
            'message': error_message
        }
        app.response_class(
            response=json.dumps(message),
            status=404,
            mimetype='application/json'
        )

    if num_builds is None or int(num_builds) < 1:
        num_builds = 1

    versions_dict = {}
    ignore_manager_above_threshold = None
    ignore_aggregator_above_threshold = None
    ignore_core_above_threshold = None
    ignore_win_collector_above_threshold = None
    ignore_linux_collector_above_threshold = None

    if '5.2.0' in base_version:
        pass
        # ignore_manager_above_threshold = 2050
        # ignore_aggregator_above_threshold = 2050
        # ignore_core_above_threshold = 2050
        # ignore_win_collector_above_threshold = 2050
        # ignore_linux_collector_above_threshold = 2050

    versions_dict.update(get_latest_versions_according_to_versions_path_as_dict(versions_path=r'X:',
                                                                                base_version=base_version,
                                                                                ignore_versions_above_threshold=ignore_manager_above_threshold,
                                                                                component_type=ComponentTypeEnum.MANAGER,
                                                                                num_build_to_return_per_component=num_builds))

    versions_dict.update(get_latest_versions_according_to_versions_path_as_dict(versions_path=r'X:',
                                                                                base_version=base_version,
                                                                                ignore_versions_above_threshold=ignore_aggregator_above_threshold,
                                                                                component_type=ComponentTypeEnum.AGGREGATOR,
                                                                                num_build_to_return_per_component=num_builds))

    versions_dict.update(get_latest_versions_according_to_versions_path_as_dict(versions_path=r'X:',
                                                                                base_version=base_version,
                                                                                ignore_versions_above_threshold=ignore_core_above_threshold,
                                                                                component_type=ComponentTypeEnum.CORE,
                                                                                num_build_to_return_per_component=num_builds))

    versions_dict.update(get_latest_versions_according_to_versions_path_as_dict(versions_path=r'X:',
                                                                                base_version=base_version,
                                                                                ignore_versions_above_threshold=ignore_win_collector_above_threshold,
                                                                                component_type=ComponentTypeEnum.WINDOWS_COLLECTOR,
                                                                                num_build_to_return_per_component=num_builds))

    versions_dict.update(get_latest_versions_according_to_versions_path_as_dict(versions_path=r'X:\linux-collector',
                                                                                base_version=base_version,
                                                                                ignore_versions_above_threshold=ignore_linux_collector_above_threshold,
                                                                                component_type=ComponentTypeEnum.LINUX_COLLECTOR,
                                                                                num_build_to_return_per_component=num_builds))

    response = app.response_class(
        response=json.dumps(versions_dict),
        status=200,
        mimetype='application/json'
    )
    return response


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host='0.0.0.0', port=5070)
