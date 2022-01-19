import json
import re
from functools import singledispatch


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
