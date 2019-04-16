# File used to ship over the contents to initialize a user cloud
# This should be used in coordination with other means to produce
# the key and profile.

# Inspired by https://stackoverflow.com/questions/34417279/sending-a-json-string-as-a-post-request/34418733
import requests

controller_addr = "http://localhost:4040"

class UserCloud:

    def __init__ (self, key, profile):
        self.key = key
        self.profile = profile
        self.address = None
        self.username = None


    def send_contents (self, addr="http://localhost:4443"):
        print (requests.get (addr + "/cloud/status").text)
        print (self.key)
        print (requests.post (addr + "/cloud/key", json=self.key).text)
        print (self.profile.algs)
        print (requests.post (addr + "/cloud/profile", json=self.profile).text)


    # Method used to get the address from speaking to the KAL
    def getaddress (self, username, addr):
        self.address = requests.post (addr + "/usercloud", json=username).text

    # Registers the user to controller
    def register_with_controller (self, controller_addr):
        print (requests.post (controller_addr + "/profile/create", json={'user':self.username}))

    def init_usercloud (self, username, controller_addr):
        self.username = username
        self.register_with_controller (controller_addr)
        self.getaddress ({'user': self.username}, controller_addr)
        self.send_contents (self.address)

    def make_post (self, addr_extension="", contents=None):
        return requests.post (self.address + addr_extension, json=contents)
