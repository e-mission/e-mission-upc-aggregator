from emission.simulation.client import EmissionFakeDataGenerator
from emission.simulation.fake_user import FakeUser
from emission.simulation.rand_helpers import gen_random_email
import argparse
import requests
from time import sleep
import numpy as np

controller_addr = "http://localhost:4040"


# Sample main to test out connecting to the user cloud setup with bottle
def main (usercount, tripcount):
    #Step1 : specify a config object for user
    client_config = {
        'emission_server_base_url': 'http://128.32.37.205:4040',
        'register_user_endpoint': '/profile/create',
        'user_cache_endpoint': '/usercache/put',
        'spawn_usercloud_endpoint': '/usercloud'
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

    fakeusers = create_fake_users (usercount, base_user_config, client_config) 
    create_and_sync_data (fakeusers, tripcount)

    
def create_fake_users (usercount, base_user_config, client_config):
    fakeusers = []
    for i in range (usercount):
        user_config = base_user_config.copy ()
        user_config["email"] = gen_random_email ()
        client = EmissionFakeDataGenerator (client_config)
        fakeusers.append (client.create_fake_user (user_config))
    return fakeusers
     

def create_and_sync_data (userlist, numTrips):
    measurements = []
    for i in range (len (userlist)):
        user_measurements = []
        for _ in range (numTrips):
            temp = userlist[i].take_trip ()
            print('# of location measurements:', len(temp))
            user_measurements.append (temp)
        print('Path:', userlist[i]._path)

    for i in range (len (userlist)):
        print (len (userlist[i]._measurements_cache))
        userlist[i].sync_data_to_server ()
        print (len (userlist[i]._measurements_cache))

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate a number of fake users and sync their data to their respective user clouds")
    parser.add_argument ("user_count", type=int,
            help="Number of users to be created")
    parser.add_argument ("trip_count", type=int,
            help="Number of trips taken by each user")
    items = parser.parse_args ()
    main (items.user_count, items.trip_count)
