import requests
import socket

from emission.net.int_service.machine_configs import controller_ip, controller_port, service_endpoint, certificate_bundle_path, privacy_budget_endpoint, load_endpoint, store_endpoint

# Class used to store pm when running the pipeline
class PM_UUID:
    def __init__(pm_addr):
        self.pm_addr = pm_addr

    def getAddress():
        return self.pm_addr

def remove_user_id_from_dicts(possible_dict):
    if isinstance(possible_dict, dict):
        if "user_id" in possible_dict:
            del possible_dict["user_id"]
        for val in possible_dict.values():
            remove_user_id_from_dicts(val)

def get_usercache_keys():
    keys_dict = dict()
    index1 = ["metadata.write_ts",
            "metadata.key"]
    key_one = "metadata.type"
    for elem in index1:
        key_one += "\n" + elem
    keys_dict[key_one] =[["ASCENDING", "ASCENDING", "ASCENDING"], "False"]
    keys_dict['metadata.write_ts'] = [["DESCENDING"], "False"]
    keys_dict['data_ts'] = [["DESCENDING"], "True"]
    return keys_dict


def get_usercache_decode_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = ["builtins", "str"]
    metadata_types["write_ts"] = ["builtins", "str"]
    metadata_types["key"] = ["builtins", "str"]
    types['metadata'] = metadata_types

    # Add data
    types['data_ts'] = ["builtins", "int"]
    return types

def get_usercache_encode_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = ["builtins", "str"]
    metadata_types["write_ts"] = ["builtins", "str"]
    metadata_types["key"] = ["builtins", "str"]
    types['metadata'] = metadata_types

    # Add data
    types['data_ts'] = ["builtins", "str"]
    return types

# Class used to replace the db
class UsercacheData:
    def __init__(self, target_address):
        self.target_address = target_address

    def store(self, data):
        return store_usercache_data(self.target_address, data)
    
    def load(self, search_fields, should_sort=False, sort=None):
        return load_usercache_data(self.target_address, search_fields, should_sort, sort) 


def store_usercache_data(target_address, data):
    return store_data(target_address, certificate_path,"Stage_usercache", 
            get_usercache_keys(), data, get_usercache_decode_types())


def load_usercache_data(target_address, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, "Stage_usercache", 
            get_usercache_keys(), search_fields, get_usercache_decode_types(), 
            get_usercache_encode_types(), should_sort, sort)

def get_calendar_keys():
    keys_dict = dict()
    index1 = ["data.attendees", "data.start_time", "data.end_time", "data.ts", "data.geo"]
    key_one = "metadata.type"
    for elem in index1:
        key_one += "\n" + elem
    keys_dict[key_one] =[["ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", 
        "ASCENDING", "GEOSPHERE"], "False"]
    return keys_dict

def get_calendar_decode_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = ["builtins", "str"]
    types['metadata'] = metadata_types

    # Add data
    data_types = dict()
    data_types["attendees"] = ["builtins", "list"]
    data_types["start_time"] = ["dateutil.parser", "parse"]
    data_types["end_time"] = ["dateutil.parser", "parse"]
    data_types["ts"] = ["dateutil.parser", "parse"]
    data_types["geo"] = ["geojson", "Point"]
    types['data'] = data_types
    return types

def get_calendar_encode_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = ["builtins", "str"]
    types['metadata'] = metadata_types

    # Add data
    data_types = dict()
    data_types["attendees"] = ["builtins", "list"]
    data_types["start_time"] = ["datetime", "datetime.isoformat"]
    data_types["end_time"] = ["datetime", "datetime.isoformat"]
    data_types["ts"] = ["datetime", "datetime.isoformat"]
    data_types["geo"] = ["geojson", "dumps"]
    types['data'] = data_types
    return types

def store_calendar_data(target_address, data):
    return store_data(target_address, certificate_path, "Stage_calendar",
            get_calendar_keys(), data, get_calendar_decode_types())

def load_calendar_data(target_address, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, certificate_path, "Stage_calendar", 
            get_calendar_keys(), search_fields, get_calendar_decode_types(),
            get_calendar_encode_types(), should_sort, sort)

def store_data(target_address, data_type, keys, data, decode_types, filter_user_id=True):
    if filter_user_id:
        remove_user_id_from_dicts(keys)
        remove_user_id_from_dicts(data)
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = data_type
        json_entries['keys'] = keys
        json_entries['data'] = data
        json_entries['decode_types'] = decode_types
        r = requests.post(target_address + store_endpoint, json=json_entries, timeout=300,
                verify=certificate_bundle_path)
    except (socket.timeout) as e:
        error = True

    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        print('Something went wrong when trying to sync your {} data.'.format(data_type))
        print(r.content)
    else:
        print("{} data sucessfully synced to the server".format(data_type))
    return error



def load_data(target_address, data_type, keys, search_fields,
        decode_types, encode_types, should_sort=False, sort=None, filter_user_id=True):
    if filter_user_id:
        remove_user_id_from_dicts(keys)
        remove_user_id_from_dicts(search_fields)
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = data_type
        json_entries['keys'] = keys
        json_entries['search_fields'] = search_fields
        json_entries['decode_types'] = decode_types
        json_entries['encode_types'] = encode_types
        if should_sort:
            json_entries['should_sort'] = "True"
            json_entries['sort'] = sort
        else:
            json_entries['should_sort'] = "False"
        r = requests.post(target_address + load_endpoint, json=json_entries, timeout=300,
                verify=certificate_bundle_path)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        print('Something went wrong when trying to load your {} data.'.format(data_type))
        print(r.content)
        return (None, error)
    else:
        print("{} data sucessfully loaded from the server".format(data_type))
        return (r.json(), error)

def request_service(username, service_name):
    controller_addr = controller_ip + ":" + str(controller_port)
    print (username)
    print (controller_addr)
    json_values = dict()
    json_values['user'] = username
    json_values['service'] = service_name
    r = requests.post (controller_addr + service_endpoint, json=json_values, verify=certificate_bundle_path)
    json_values = r.json()
    return json_values['addresses']

def deduct_privacy(target_address, cost):
    r = requests.post (target_address + privacy_budget_endpoint, json={'cost': cost}, verify=certificate_bundle_path)
    print(r.text)
    return r.json()

