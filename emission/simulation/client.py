from abc import ABC, abstractmethod
from emission.simulation.fake_user import FakeUser
from emission.simulation.error import AddressNotFoundError
import emission.simulation.gen_profile as gp
import emission.simulation.connect_usercloud as escu
import requests
import numpy as np

UMAX_64 = int (np.power (2.0, 64))

class Client(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def create_fake_user(self, config):
        pass 
    @abstractmethod
    def _parse_user_config(self, config):
        pass  

def random_64s (count):
    val = 0
    for i in range (count):
        val <<= 6
        val += int (np.random.randint (low=0, high=UMAX_64, dtype="uint64"))
    return val

class EmissionFakeDataGenerator(Client):
    def __init__(self, config):
        #TODO: Check that the config object has keys: emission_server_base_url, register_user_endpoint, user_cache_endpoint
        self._config = config
        self._user_factory = FakeUser
        # Additional info for user cloud
        key = random_64s (32)
        profile = gp.AlgProfile ()
        # Add all known algs to default algs.
        profile.add_all_to_default_algs()
        self._usercloud = escu.UserCloud (key, profile)

    def create_fake_user(self, config):
        #TODO: parse the config object
        uuid = self._register_fake_user(config['email'])
        config['uuid'] = uuid
        config['upload_url'] = self._usercloud.address + self._config['user_cache_endpoint']
        #config['pipeline_url'] = self._usercloud.address + self._config['algorithm_endpoint']
        return self._user_factory(config)

    def _register_fake_user(self, email):
        data = {'user': email}
        #url = self._config['emission_server_base_url'] + self._config['register_user_endpoint'] 
        self._usercloud.init_usercloud (data, self._config['emission_server_base_url'])
        r = requests.post(self._usercloud.address + self._config['register_user_endpoint'], json=data)
        r.raise_for_status()
        uuid = r.json()['uuid']
        #TODO: This is a hack to make all the genereated entries JSON encodeable. 
        #Might be a bad Idead to stringify the uuid. For instance, 
        # the create_entry function expects uuid of type UUID
        return str(uuid)

    def _parse_user_config(self, config):
        #TODO: This function shoudl be used to parser user config object and check that the paramaters are valid.
        try: 
            locations = config['locations']
        except KeyError:
            print("You must specify a set of addresses")
            raise AddressNotFoundError

        #check that all addresses are supported by the trip planner software
        #for address in addresses:
        #    if not self._trip_planer_client.has_address(address):
        #        message = ("%s, is not supported by the Trip Planer", address) 
        #        raise AddressNotFoundError(message, address)

        #check that all teh transition probabilites for every address adds up to one

        
