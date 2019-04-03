# File used to ship over the contents to initialize a user cloud
# This should be used in coordination with other means to produce
# the key and profile.

# Inspired by https://stackoverflow.com/questions/34417279/sending-a-json-string-as-a-post-request/34418733
from emission.simulation.gen_profile import AlgProfile 
import requests
import numpy as np

controller_port = 4040

class UserCloud:

    def __init__ (self, key, profile):
        self.key = key
        self.profile = profile
        self.address = None

    def send_contents (self, addr="http://localhost:4443"):
        print (requests.get (addr + "/cloud/status").text)
        print (self.key)
        print (requests.post (addr + "/cloud/key", json=self.key).text)
        print (self.profile.algs)
        print (requests.post (addr + "/cloud/profile", json=self.profile.algs).text)


    # Method used to get the address from speaking to the KAL
    def getaddress (self, username):
        self.address = requests.post ("http://localhost:" + str (controller_port) + "/usercloud", json=username).text

    def init_usercloud (self, username):
        self.getaddress (username)
        self.send_contents (self.address)

    def make_post (self, addr_extension="", contents=None):
        return requests.post (self.address + addr_extension, json=contents)

# Sample main to test out connecting to the user cloud setup with bottle
def main ():
    key_list = []
    profile_list = []
    names = ["Nick", "Jack"]
    for i in range (2):
        key_list.append (np.random.randint (low=0, high=(pow(2, 63) - 1)))
        profile_list.append (AlgProfile ())
    user_list = []
    for i in range (2):
        user_list.append (UserCloud (key_list[i], profile_list[i]))
    alg_contents = dict ()
    alg_contents["algorithm"] = list (user_list[0].profile.algs.keys ())[0]
    for j in range (2):
        for i in range (2):
            user_list[i].init_ usercloud (names[i])
            alg_contents["algorithm"] = list (user_list[i].profile.algs.keys ())[0]
            print (user_list[i].make_post ("/run/useralg", alg_contents).text)
            alg_contents["algorithm"] = "Not an algorithm"
            print (user_list[i].make_post ("/run/useralg", alg_contents).text)

if __name__ == "__main__":
    main ()
