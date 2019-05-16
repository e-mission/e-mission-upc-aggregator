from emission.simulation.client import EmissionFakeDataGenerator
from emission.simulation.fake_user import FakeUser
from emission.simulation.rand_helpers import gen_random_email
import argparse
import requests
from time import sleep
import numpy as np
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint, user_cache_endpoint, spawn_usercloud_endpoint
from multiprocessing.dummy import Pool

controller_addr = "{}:{}".format (controller_ip, controller_port)


# Sample main to test out connecting to the user cloud setup with bottle
def main (usercount, tripcount):
    #Step1 : specify a config object for user
    client_config = {
        'emission_server_base_url': controller_addr,
        'register_user_endpoint': register_user_endpoint,
        'user_cache_endpoint': user_cache_endpoint,
        'spawn_usercloud_endpoint': spawn_usercloud_endpoint
    }

    base_user_config = {
        "email" : "", #Fill this in later for each user
    
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

    for i in range((usercount / 50) + 1)
        curr_num_users = (usercount - 50 * i) % 51
        fakeusers = create_fake_users (curr_num_users, base_user_config, client_config) 
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
    pool = Pool ()
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (create_user_data, [userlist[i], numTrips]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()

    pool = Pool (len (userlist) + 1)
    results = []
    for i in range (len (userlist)):
        results.append (pool.apply_async (sync_user_data, [userlist[i]]))
    pool.close ()
    [result.wait () for result in results]
    pool.join ()
    print ([result.get () for result in results])

def create_user_data (user, numTrips):
    for _ in range (numTrips):
        temp = user.take_trip ()

def sync_user_data (user):
    old_len = len (user._measurements_cache)
    user.sync_data_to_server ()
    new_len = len (user._measurements_cache)
    return (old_len, new_len)

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate a number of fake users and sync their data to their respective user clouds")
    parser.add_argument ("user_count", type=int,
            help="Number of users to be created")
    parser.add_argument ("trip_count", type=int,
            help="Number of trips taken by each user")
    items = parser.parse_args ()
    main (items.user_count, items.trip_count)
