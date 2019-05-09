from emission.simulation.client import EmissionFakeDataGenerator
from emission.simulation.fake_user import FakeUser
from emission.simulation.data_sync import create_and_sync_data
import requests
from time import sleep
import numpy as np

controller_addr = "http://localhost:4040"


# Sample main to test out connecting to the user cloud setup with bottle
def main ():
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
    
    usernames = ["Nick", "Jack", "Shankari", "Kate", "Alvin", "Hersh"]
    fakeusers = []
    for name in usernames:
        user_config = base_user_config.copy ()
        user_config["email"] = "{}@emission-example-user".format (name)
        client = EmissionFakeDataGenerator (client_config)
        fakeusers.append (client.create_fake_user (user_config))

    create_and_sync_data (fakeusers, 10)
        
        

if __name__ == "__main__":
    main ()
