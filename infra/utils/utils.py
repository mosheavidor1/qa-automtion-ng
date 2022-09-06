import json
import random
import re
import string

import allure
import requests
from functools import singledispatch

from infra.allure_report_handler.reporter import Reporter
from infra.enums import HttpRequestMethodsEnum


@singledispatch
def remove_null_bool(ob):
    return ob


@remove_null_bool.register(list)
def _process_list(ob):
    return [remove_null_bool(v) for v in ob]


@remove_null_bool.register(dict)
def _process_list(ob):
    return {k: remove_null_bool(v) for k, v in ob.items()
            if v is not None and v is not True and v is not False}


class StringUtils:

    @staticmethod
    def generate_random_string(length=10):
        characters = string.ascii_letters + string.digits  # + string.punctuation
        rand_str = ''.join(random.choice(characters) for _ in range(length))
        return rand_str

    @staticmethod
    def is_digit_in_string(text):
        return any(str.isdigit(c) for c in text)

    @staticmethod
    def get_ip_port_as_tuple(text):
        """
        This method gets ip:port (127.0.0.1:8081) as input and return (127.0.0.1, 8081) as tuple
        :param text: 127.0.0.1:8081
        :return: (127.0.0.1, 8081) as tuple
        """
        if ':' not in text or text is None:
            return None, None

        splitted = text.split(':')

        ip_addr = splitted[0]
        port = splitted[1]
        return ip_addr, port

    @staticmethod
    def get_txt_by_regex(text: str, regex: str, group: int = None):
        if text is None:
            ValueError("text param can not be None")

        result = re.search(regex, text)
        if result is not None and group is not None:
            result = result.group(group)

        return result


class JsonUtils:

    @staticmethod
    def object_to_json(obj, null_sensitive=True, sort_keys=False, indent=4):
        json_obj = json.dumps(obj, default=lambda o: o.__dict__, sort_keys=sort_keys, indent=indent)

        if null_sensitive:
            source = json.loads(json_obj)
            json_obj = json.dumps(remove_null_bool(source), sort_keys=sort_keys, indent=indent)

        return json_obj


class DictionaryUtils:

    @staticmethod
    def merge_dicts(*dicts):
        all_keys = {k for d in dicts for k in d.keys()}
        return {k: [d[k] for d in dicts if k in d] for k in all_keys}

    @staticmethod
    def get_dictionary_diff(first_dict, second_dict):
        value = {k: second_dict[k] for k in set(second_dict) - set(first_dict)}
        return value


class HttpRequesterUtils:

    @staticmethod
    @allure.step("Going to send an HTTP request")
    def send_request(request_method: HttpRequestMethodsEnum,
                     url: str,
                     auth: tuple = None,
                     headers: dict = None,
                     body: dict = None,
                     expected_status_code: int = 200,
                     verify_tls_certificate: bool = True,
                     dumps_the_body=True):

        Reporter.attach_str_as_file(file_name='request_method', file_content=request_method.name)
        Reporter.attach_str_as_file(file_name='url', file_content=url)

        if headers is not None:
            Reporter.attach_str_as_file(file_name='headers', file_content=json.dumps(headers, indent=4))

        if body is not None:
            Reporter.attach_str_as_file(file_name='body', file_content=json.dumps(body, indent=4))

        response = None
        match request_method:

            case HttpRequestMethodsEnum.GET:
                response = requests.get(url=url, auth=auth, headers=headers, verify=verify_tls_certificate)

            case HttpRequestMethodsEnum.POST:
                if dumps_the_body is True:
                    body = json.dumps(body) if body is not None else body
                response = requests.post(url=url, auth=auth, headers=headers, data=body, verify=verify_tls_certificate)

            case HttpRequestMethodsEnum.PUT:
                if dumps_the_body is True:
                    body = json.dumps(body) if body is not None else body
                response = requests.put(url=url, auth=auth, headers=headers, data=body, verify=verify_tls_certificate)

            case HttpRequestMethodsEnum.DELETE:
                response = requests.delete(url=url, auth=auth, headers=headers, verify=verify_tls_certificate)

            case HttpRequestMethodsEnum.CONNECT | \
                    HttpRequestMethodsEnum.HEAD | \
                    HttpRequestMethodsEnum.OPTIONS | \
                    HttpRequestMethodsEnum.TRACE:
                raise Exception(f"There is not implementation for {request_method.name}, sorry :(")

        Reporter.attach_str_as_file(file_name='response status code', file_content=str(response.status_code))

        if expected_status_code != response.status_code:
            if not (expected_status_code == 200 and response.status_code == 201):
                assert False, (
                    f"expected status code is: {expected_status_code}, actual status code is: {response.status_code}"
                )

        try:
            content = json.loads(response.content)
        except json.decoder.JSONDecodeError:
            content = str(response.content)

        Reporter.attach_str_as_file(file_name='response body', file_content=json.dumps(content, indent=4))

        return content
