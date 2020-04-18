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

def store_usercache_data(target_address, certificate_path, data):
    store_data(target_address, "Stage_usercache", get_usercache_keys(), data, certificate_path)


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
    keys_dict[key_one] =[["ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", "GEOSPHERE"], "False"]
    return keys_dict

def store_calendar_data(target_address, certificate_path, data):
    store_data(target_address, "Stage_calendar", get_calendar_keys(), data, certificate_path)

def load_calendar_data(target_address, certificate_path, search_fields, 
        should_sort=False, sort=None):
    return load_data(target_address, certificate_path, "Stage_calendar", 
            get_calendar_keys(), search_fields, should_sort, sort)

def store_data(target_address, certificate_path, data_type, keys, data):
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = data_type
        json_entries['keys'] = keys
        json_entries['data'] = data
        r = requests.post(target_address, json=json_entries, timeout=300, verify=certificate_path)
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



def load_data(target_address, certificate_path, data_type, keys, search_fields, should_sort=False, sort=None):
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
        r = requests.post(target_address, json=json_entries, timeout=300, verify=certificate_path)
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        print('Something went wrong when trying to load your {} data.'.format(data_type))
        print(r.content)
    else:
        return r.text
