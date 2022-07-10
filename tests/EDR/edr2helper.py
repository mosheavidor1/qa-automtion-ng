import datetime
import json
import time
from deepdiff import DeepDiff
import ast
from functools import reduce
import string



class EdrHelper:


    def get_collector_time(self, col):
        collectortime = int(col.win_agent.conn.modules.time.time())
        # this is to comply with the weird time in the event, 13 digits milliseconds
        t = int(str(collectortime)[0:10]) * 1000
        return t

    def verify_event(self, collector, query, category="", timeout=300):
        time.sleep(5)
        self.log.info(f'running the following query: {query} category {category}')
        for a in range(0, int(timeout / 10)):
            res = self.rest.edr2_count(devices=[collector.host_name], category=category, query=query)
            if res['all'] != 1:
                self.log.info(f' no event yet. {str(res)}, waiting 5 more seconds')
                time.sleep(5)
                continue
            else:
                res = self.rest.edr2_search(devices=[collector.host_name], category=category, query=query)[0]
                self.log.info(f'{collector.ip} - Got the event for the desired query {query}')
                self.log.info(f'{collector.ip} event json - {str(res)}')
                return True
        self.log.error(f'OOPS - did not get an event after {timeout} seconds')
        return False

    def verify_type_exists(self, collector, query, category="", timeout=300):
        time.sleep(5)
        self.log.info(f'running query: {query} of category: {category}')
        for a in range(0, int(timeout / 10)):
            res = self.rest.edr2_count(devices=[collector.host_name], category=category, query=query)
            if res['all'] < 1:
                self.log.info(f' no event yet. {str(res)}, waiting 5 more seconds')
                time.sleep(5)
                continue
            else:
                self.log.info(f'{collector.ip} - Event type exists for query: {query}')
                return True
        self.log.error(f'Event type was not found after {timeout} seconds')
        return False

    def get_event(self, collector, query, category="", timeout=400):
        time.sleep(5)
        self.log.info(f'running the following query: {query} category {category}')
        for a in range(0, int(timeout / 10)):
            res = self.rest.edr2_count(devices=[collector.host_name], category=category, query=query)
            if res['all'] == 0:
                self.log.info(f' no event yet. {str(res)}, waiting 5 more seconds')
                time.sleep(5)
                continue
            elif res['all'] == 1:
                res = self.rest.edr2_search(devices=[collector.host_name], category=category, query=query)[0]
                self.log.info(f'{collector.ip} - Got the event for the desired query {query}')
                self.log.info(f'{collector.ip} event json - {self.stringify_event(res)}')
                return res
            else:
                self.log.info(f' Error: More than 1 event was found! {str(res)}')
                return False

        self.log.error(f'OOPS - did not get an event after {timeout} seconds')
        return False

    def get_command_result(self, collector, command):
        return json.loads(collector.run_command(command))

    def get_expected(self, file_name):
        folder_name = f'expected-events-{self.version_dict[self.collector_version.rpartition(".")[0]]}'

        with open(f"{self.COMMON_PATH}\\expected\\{folder_name}\\{file_name}", "r") as json_file:
            return json.load(json_file)[0]

    def assert_comparison(self, actual, ignored_keys, file_name):
        if not actual:
            return False
        else:
            expected = self.get_expected(file_name)
        return self.compare_events(actual, expected, ignored_keys)

    def get_ignored_keys(self, *target):
        """
        pass the required name of group of keys. e.g "process", "process-creation-process"....etc
        :param version_is_hf1: condition for HF1 version. True says it's HF1, False otherwise
        :param target: target group of keys to ignore
        :return: the list of keys to ignore
        """
        folder_name = f'ignored-keys-{self.version_dict[self.collector_version.rpartition(".")[0]]}'

        with open(f"{self.COMMON_PATH}\\ignored\\{folder_name}\\edr-ignored-fields.json",
                  "r") as json_file:
            content = json.load(json_file)

            ignored = content["common"]
            if len(target) > 0 and target[0] in ("file-detected", "log-entry-created"):
                ignored = []
            for t in target:
                ignored = ignored + content[t.lower()]
        return ignored

    def resolve_path(self, dictionary, path):
        return reduce(dict.get, path, dictionary)

    def del_endpoint(self, dictionary, path):
        if isinstance(path, list):
            path = tuple(path)
        parent_path, last = path[:-1], path[-1]
        parent = self.resolve_path(dictionary, parent_path)
        del parent[last]

    def compare_events(self, expected_json, actual_json, values_to_ignore):
        """
        :param expected_json: the expected json to compare
        :param actual_json: the actual result from the event
        :param values_to_ignore:  list of keys/sub dict to be remove or to be update, for example if you want to remove simple key (not sub dict)
         and value from sub dict the list should be like this: ["ID","Target": {"Process": {"User": None}]
        :return: True if equal False if not
        """
        for key in values_to_ignore:
            if isinstance(key, str):
                del expected_json[key]
                del actual_json[key]
            else:
                try:
                    self.del_endpoint(expected_json, key)
                    self.del_endpoint(actual_json, key)
                except:
                    self.log.error(f"failed to delete key: {key}")
                    return False

        diff = DeepDiff(expected_json, actual_json).to_json()
        diff_dict = ast.literal_eval(diff)
        if len(diff_dict) == 0:
            self.log.info("events are equal")
            return True
        else:
            self.log.error(f"jsons are not equal!, diff: {diff}")
            return False

    def stringify_event(self, res):
        printable = set(string.printable)
        str_res = ''.join(filter(lambda x: x in printable, str(res)))
        return str_res

    def search_tag_by_name(self, tag_name, timeout=30):
        """
        :param timeout: the time the function attempts to get response
        :param tag_name: the name of the tag to search
        :return: True if the tag exists, False otherwise
        """
        for a in range(0, int(timeout / 10)):
            res = self.rest.edr2_list_tags()
            if len(res) < 1:
                self.log.info(f'Empty tag list. {str(res)}, waiting 5 more seconds')
                time.sleep(3)
                continue
            else:
                for tag in res:
                    if tag['tagName'] == tag_name:
                        return True
        self.log.error(f'Failed to get tag after {timeout} seconds')
        return False

    def get_tag_by_name(self, tag_name, timeout=30):
        """
        :param timeout: the time the function attempts to get response
        :param tag_name: the name of the tag to search
        :return: tagId if the tag exists, False otherwise
        """
        for a in range(0, int(timeout / 10)):
            res = self.rest.edr2_list_tags()
            if len(res) < 1:
                self.log.info(f'Empty tag list. {str(res)}, waiting 5 more seconds')
                time.sleep(3)
                continue
            else:
                for tag in res:
                    if tag['tagName'] == tag_name:
                        return tag['tagId']
        self.log.error(f'Failed to get tag after {timeout} seconds')
        return False

    def get_scheduled_query_range(self, time):
        """
        :param save_time: the time the scheduled query was saved
        :return: the start and end times of the schedule
        """
        hour = time.hour
        minute = time.minute

        if 0 <= minute < 15:
            return f'{time.date()} {hour}:00:00', f'{time.date()} {hour}:15:00'
        elif 15 <= minute < 30:
            return f'{time.date()} {hour}:15:00', f'{time.date()} {hour}:30:00'
        elif 30 <= minute < 45:
            return f'{time.date()} {hour}:30:00', f'{time.date()} {hour}:45:00'
        else:
            return f'{time.date()} {hour}:45:00', f'{time.date()} {hour+1}:15:00'
