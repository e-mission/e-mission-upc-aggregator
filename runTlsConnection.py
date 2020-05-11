import subprocess, time
import sys
import requests
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint

import urllib3
urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)


controller_addr = "{}:{}".format (controller_ip, controller_port)

def main ():
    query_file = "query.json"
    subprocess.Popen (["mkdir", "-p", "csvs"], cwd="./")
    num_users = [1]
    num_trips = [10]
    num_queries = 1
    for curr_num_users in num_users:
        for curr_num_trips in num_trips:
            #requests.post (controller_addr + "/setup_networks")
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(curr_num_users), str(curr_num_trips)], cwd="./")
            ret.wait ()
#            requests.post (controller_addr + "/clear_containers")


if __name__ == "__main__":
    main ()
