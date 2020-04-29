import requests
import socket
from emission.net.int_service.machine_configs import controller_ip, controller_port, service_endpoint, certificate_bundle_path, privacy_budget_endpoint

#FIXME

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
    return store_data(target_address, "Stage_calendar",
            get_calendar_keys(), data, get_calendar_decode_types())

def load_calendar_data(target_address, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, "Stage_calendar", 
            get_calendar_keys(), search_fields, get_calendar_decode_types(),
            get_calendar_encode_types(), should_sort, sort)


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

