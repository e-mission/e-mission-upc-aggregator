from emission.simulation.client import EmissionFakeDataGenerator
from emission.simulation.fake_user import FakeUser
from emission.simulation.rand_helpers import gen_random_email
import argparse
import requests
from time import sleep
import numpy as np
import datetime
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint, load_endpoint, service_endpoint
from multiprocessing.dummy import Pool
import Compute_Layer.shared_resources.stream_data as clsrsd
from Compute_Layer.shared_resources.ical import calendarTimeZone 
from emission.net.int_service.machine_configs import certificate_bundle_path
from dateutil.parser import parse
import geojson
from Compute_Layer.Services.queries.queries import receive_query

controller_addr = "{}:{}".format (controller_ip, controller_port)


# Sample main to test out connecting to the user cloud setup with bottle
def main (usercount, tripcount):
    #Step1 : specify a config object for user
    client_config = {
        'emission_server_base_url': controller_addr,
        'register_user_endpoint': register_user_endpoint,
        'load_endpoint': load_endpoint,
        'service_endpoint': service_endpoint
    }

    base_user_config = {
        "email" : "", #Fill this in later for each user
        "uuid" : "",  #Dummy entry to allow reuse
    
        "locations" :
        [
            {
                'label': 'home',
                'coordinate': [37.77264255,-122.399714854263]
            },

            {
                'label': 'work',
                'coordinate': [37.42870635,-122.140926605802]
            }
        ],

        "transition_probabilities":
            [
                np.array([0, 1]),
                np.array([1, 0])
            ],
    
        "modes" : 
            {
                "CAR" : [['home', 'work'], ['work', 'home']]
            },

        "default_mode": "CAR",
        "initial_state" : "home",
        "radius" : ".1"
    }

    for i in range(int(usercount / 50) + 1):
        curr_num_users = (usercount - 50 * i) % 51
        fakeusers = create_fake_users (curr_num_users, base_user_config, client_config) 
        print("REACHED!")
        create_and_sync_data (fakeusers, tripcount)

    
def create_fake_users (usercount, base_user_config, client_config):
    pool = Pool (usercount + 1)
    fakeusers = []
    for i in range (usercount):
        user_config = base_user_config.copy ()
        user_config["email"] = gen_random_email ()
        fakeusers.append (pool.apply_async (connect_user, [client_config, user_config]))
    pool.close ()
    [result.wait () for result in fakeusers]
    pool.join ()
    return [result.get () for result in fakeusers]
    
def connect_user (client_config, user_config): 
    client = EmissionFakeDataGenerator (client_config)
    return client.create_fake_user (user_config)

def create_and_sync_data (userlist, numTrips):
    # Open use once OTP server works
    """
    pool = Pool ()
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (create_user_data, [userlist[i], numTrips]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    """

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (sync_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (update_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (delete_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (sync_user_data_dep, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (update_user_data_dep, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    """
    # Example test calendar
    test_calendar = "Compute_Layer/Services/Calendar/example_cal.txt"

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (sync_calendar_data, [userlist[i], test_calendar]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    for i in range (len (userlist)):
        results.append (pool.apply_async (load_calendar_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    target_date = datetime.datetime(2020, 3, 15, tzinfo=calendarTimeZone)
    for i in range (len (userlist)):
        results.append (pool.apply_async (get_arrival_time, [userlist[i], target_date]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_sum_query, [userlist[i], 1501592400, 1564664400, .01, 10]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_sum_query, [userlist[i], 1601592400, 1664664400, .01, 10]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_ae_query, [userlist[i], 1501592400, 1564664400, .01, 10]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_ae_query, [userlist[i], 1601592400, 1664664400, .01, 10]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])
    
    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_rc_query, [userlist[i], 1501592400, 1564664400, .01, 10, 30]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (launch_rc_query, [userlist[i], 1601592400, 1664664400, .01, 10, 30]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])
    """

def create_user_data (user, numTrips):
    for _ in range (numTrips):
        temp = user.take_trip ()

def sync_user_data (user):
    old_len = len (user._measurements_cache)
    user.sync_data_to_server ()
    new_len = len (user._measurements_cache)
    return (old_len, new_len)

def sync_user_data_dep (user):
    old_len = len (user._measurements_cache)
    user.sync_data_dep_to_server ()
    new_len = len (user._measurements_cache)
    return (old_len, new_len)

def update_user_data (user):
    data = user.update_data_to_server()
    return data

def update_user_data_dep (user):
    data = user.update_data_dep_to_server()
    return data

def delete_user_data (user):
    data = user.delete_data_from_server()
    return data

def load_user_data (user):
    data = user.load_data_from_server()
    return data

def sync_calendar_data(user, calendar_file):
    user.sync_calendar_to_server(calendar_file)

def load_calendar_data(user):
    return user.load_calendar_from_server()

def get_arrival_time(user, date):
    addresses = clsrsd.request_service({'user': user._config['email']}, 'calendar')
    json_dict = dict()
    json_dict['pm_address'] = addresses[0]
    json_dict['date'] = date.isoformat()
    r = requests.post (addresses[1] + "/get_last_event", json=json_dict, verify=certificate_bundle_path)
    return r.json()

def launch_sum_query(user, start_ts, end_ts, alpha, offset):
    query = dict()
    query['query_type'] = "sum"
    query['start_ts'] = start_ts
    query['end_ts'] = end_ts
    query['alpha'] = alpha
    query['offset'] = offset
    return launch_query(user, query)

def launch_ae_query(user, start_ts, end_ts, alpha, offset):
    query = dict()
    query['query_type'] = "ae"
    query['start_ts'] = start_ts
    query['end_ts'] = end_ts
    query['alpha'] = alpha
    query['offset'] = offset
    return launch_query(user, query)

def launch_rc_query(user, start_ts, end_ts, alpha, r_start, r_end): 
    query = dict()
    query['query_type'] = "rc"
    query['start_ts'] = start_ts
    query['end_ts'] = end_ts
    query['alpha'] = alpha
    query['offset'] = (r_end - r_start) / 2
    return launch_query(user, query)

def launch_query(user, query):
    addresses = clsrsd.request_service({'user': user._config['email']}, 'query')
    json_dict = dict()
    json_dict['pm_address'] = addresses[0]
    json_dict['query'] = query
    r = requests.post (addresses[1] + "/receive_query", json=json_dict, verify=certificate_bundle_path)
    return r.json()

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate a number of fake users and sync their data to their respective user clouds")
    parser.add_argument ("user_count", type=int,
            help="Number of users to be created")
    parser.add_argument ("trip_count", type=int,
            help="Number of trips taken by each user")
    items = parser.parse_args ()
    main (items.user_count, items.trip_count)

