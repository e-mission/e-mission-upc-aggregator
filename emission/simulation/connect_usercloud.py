# File used to ship over the contents to initialize a user cloud
# This should be used in coordination with other means to produce
# the key and profile.

# Inspired by https://stackoverflow.com/questions/34417279/sending-a-json-string-as-a-post-request/34418733
import requests
from emission.net.int_service.machine_configs import register_user_endpoint, service_endpoint, cloud_key_endpoint
import emission.simulation.profile_json as profile_json
from Compute_Layer.shared_resources.fake_mongo_types import request_service 

class UserCloud:

    def __init__ (self, key):
        self.key = key
        self.address = None
        self.username = None


    def send_contents (self, addr):
        print(addr)
        print (requests.post (addr + cloud_key_endpoint, json=self.key).text)


    # Method used to get the address from speaking to the KAL
    def getaddress (self):
        self.address = request_service(self.username, 'PM')[0]

    # Registers the user to controller
    def register_with_controller (self, controller_addr):
        print (controller_addr)
        print (requests.post (controller_addr + register_user_endpoint, json={'user':self.username}))

    def init_usercloud (self, username, controller_addr):
        self.username = username
        #self.register_with_controller (controller_addr)
        #self.getaddress ()
        self.address = "http://192.168.99.100:30000"
        self.send_contents (self.address)

    def make_post (self, addr_extension="", contents=None):
        return requests.post (self.address + addr_extension, json=contents)
