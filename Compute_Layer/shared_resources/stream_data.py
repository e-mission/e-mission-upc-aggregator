def get_calendar_keys():
    keys_dict = dict()
    index1 = ["data.attendees", "data.start_time", "data.end_time", "data.ts", "data.geo"]
    key_one = "metadata.type"
    for elem in index1:
        key_one += "\n" + elem
    keys_dict[key_one] =[["ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", "ASCENDING", "GEOSPHERE"], "False"]
    return keys_dict

def store_calendar_data(target_address, data, certificate_path):
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = "Stage_calendar"
        json_entries['keys'] = get_calendar_keys()
        json_entries['data'] = data
        r = requests.post(target_address, json=json_entries, timeout=300, verify=certificate_path)
    except (socket.timeout) as e:
        error = True

    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        print('Something went wrong when trying to sync your calendar data.')
        print(r.content)
    else:
        print("calendar data sucessfully synced to the server")

def load_calendar_data(target_address, data, certificate_path):
    error = False
    try:
        json_entries = dict()
        json_entries['data_type'] = "Stage_calendar"
        json_entries['keys'] = get_calendar_keys()
        json_entries['search_fields'] = [{"metadata.type": "calendar"}, {"_id": "False"}]
        json_entries['should_sort'] = "True"
        json_entries['sort'] = {'data.end_time': "False"}
        r = requests.post(target_address, json=json_entries, timeout=300, verify=certificate_path)
    except (socket.timeout) as e:
        error = True

    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        print('Something went wrong when trying to load your calendar data.')
        print(r.content)
    else:
        return r.text
