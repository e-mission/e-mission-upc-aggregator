# File used to ship over the contents to initialize a user cloud
# This should be used in coordination with other means to produce
# the key and profile.

# Inspired by https://stackoverflow.com/questions/34417279/sending-a-json-string-as-a-post-request/34418733
from gen_profile import AlgProfile 
import requests
import numpy as np

kal_port = 8080

class UserCloud:

    def __init__ (self, key, profile):
        self.key = key
        self.profile = profile

    def send_contents (self, addr="http://localhost:4443"):
        print (requests.get (addr + "/status").text)
        print (self.key)
        print (requests.post (addr + "/key", json=self.key).text)
        print (self.profile.algs)
        print (requests.post (addr + "/profile", json=self.profile.algs).text)


# Method used to get the address from speaking to the KAL
def getaddress (username):
    return requests.post ("http://localhost:" + str (kal_port) + "/usercloud", json=username).text

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
    for i in range (2):
        addr = getaddress (names[i])
        user_list[i].send_contents (addr)
        alg_contents["algorithm"] = list (user_list[i].profile.algs.keys ())[0]
        print (requests.post (addr + "/run", json=alg_contents).text)
        alg_contents["algorithm"] = "Not an algorithm"
        print (requests.post (addr + "/run", json=alg_contents).text)
    for i in range (2):
        addr = getaddress (names[i])
        user_list[i].send_contents (addr)
        alg_contents["algorithm"] = list (user_list[i].profile.algs.keys ())[0]
        print (requests.post (addr + "/run", json=alg_contents).text)
        alg_contents["algorithm"] = "Not an algorithm"
        print (requests.post (addr + "/run", json=alg_contents).text)

if __name__ == "__main__":
    main ()
