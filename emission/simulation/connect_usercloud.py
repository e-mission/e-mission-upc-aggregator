# File used to ship over the contents to initialize a user cloud
# This should be used in coordination with other means to produce
# the key and profile.

# Inspired by https://stackoverflow.com/questions/34417279/sending-a-json-string-as-a-post-request/34418733
import requests
from emission.net.int_service.machine_configs import register_user_endpoint, spawn_usercloud_endpoint, cloud_status_endpoint, cloud_key_endpoint, cloud_profile_endpoint
import emission.simulation.profile_json as profile_json

class UserCloud:

    def __init__ (self, key, profile):
        self.key = key
        self.profile = profile
        self.address = None
        self.username = None


    def send_contents (self, addr):
        print (requests.get (addr + cloud_status_endpoint).text)
        print (requests.post (addr + cloud_key_endpoint, json=self.key).text)
        print (requests.post (addr + cloud_profile_endpoint, json=profile_json.to_json(self.profile)).text)


    # Method used to get the address from speaking to the KAL
    def getaddress (self, username, addr):
        self.address = requests.post (addr + spawn_usercloud_endpoint, json=username).text

    # Registers the user to controller
    def register_with_controller (self, controller_addr):
        print (controller_addr)
        print (requests.post (controller_addr + register_user_endpoint, json={'user':self.username}))

    def init_usercloud (self, username, controller_addr):
        self.username = username
        self.register_with_controller (controller_addr)
        self.getaddress ({'user': self.username}, controller_addr)
        self.send_contents (self.address)

    def make_post (self, addr_extension="", contents=None):
        return requests.post (self.address + addr_extension, json=contents)
