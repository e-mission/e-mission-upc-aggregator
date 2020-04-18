import requests
import socket

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


def get_usercache_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = "builtins.str"
    metadata_types["write_ts"] = "builtins.str"
    metadata_types["key"] = "builtins.str"
    types['metadata'] = metadata_types

    # Add data
    types['data_ts'] = "builtins.str"
    return types

def store_usercache_data(target_address, certificate_path, data):
    return store_data(target_address, certificate_path,"Stage_usercache", 
            get_usercache_keys(), data, get_usercache_types())


def load_usercache_data(target_address, certificate_path, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, certificate_path, "Stage_usercache", 
            get_usercache_keys(), search_fields, should_sort, sort)

def get_calendar_keys():
    keys_dict = dict()
    index1 = ["data.attendees", "data.start_time", "data.end_time", "data.ts", "data.geo"]
    key_one = "metadata.type"
    for elem in index1:
        key_one += "\n" + elem
    keys_dict[key_one] =[["ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", 
        "ASCENDING", "GEOSPHERE"], "False"]
    return keys_dict

def get_calendar_types():
    types = dict()

    # Add metadata
    metadata_types = dict()
    metadata_types["type"] = "builtins.str"
    types['metadata'] = metadata_types

    # Add data
    data_types = dict()
    data_types["attendees"] = "datetime.datetime"
    data_types["start_time"] = "datetime.datetime"
    data_types["end_time"] = "datetime.datetime"
    data_types["ts"] = "datetime.datetime"
    data_types["geo"] = "builtins.list"
    types['data'] = data_types
    return types

def store_calendar_data(target_address, certificate_path, data):
    return store_data(target_address, certificate_path, "Stage_calendar",
            get_calendar_keys(), data, get_calendar_types())

def load_calendar_data(target_address, certificate_path, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, certificate_path, "Stage_calendar", 
            get_calendar_keys(), search_fields, should_sort, sort)

def store_data(target_address, certificate_path, data_type, keys, data, types):
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = data_type
        json_entries['keys'] = keys
        json_entries['data'] = data
        json_entries['types'] = types
        r = requests.post(target_address, json=json_entries, timeout=300,
                verify=certificate_path)
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



def load_data(target_address, certificate_path, data_type, keys, search_fields,
        should_sort=False, sort=None):
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = data_type
        json_entries['keys'] = keys
        json_entries['search_fields'] = search_fields
        if should_sort:
            json_entries['should_sort'] = "True"
            json_entries['sort'] = sort
        else:
            json_entries['should_sort'] = "False"
        r = requests.post(target_address, json=json_entries, timeout=300,
                verify=certificate_path)
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
        return (r.text, error)
