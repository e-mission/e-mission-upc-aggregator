import subprocess, time
import sys
import requests
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint


controller_addr = "{}:{}".format (controller_ip, controller_port)

def main ():
    query_file = "query.json"
    subprocess.Popen (["mkdir", "-p", "csvs"], cwd="./")
    num_users = [3, 500, 1000]
    num_trips = [10, 50, 100]
    num_queries = 30
    for curr_num_users in num_users:
        for curr_num_trips in num_trips:
            requests.post (controller_addr + "/setup_networks")
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(curr_num_users), str(curr_num_trips)], cwd="./")
            ret.wait ()
            # for i in range (1, 11, 1):
            #     i = i * .1
            for _ in range(num_queries):
                requests.post (controller_addr + "/pause_all_queriers")
                requests.post (controller_addr + "/pause_all_clouds")
                csv_file_name = "csvs/time_" + str(curr_num_users) + "_" + str(curr_num_trips) + ".csv"
                ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", query_file, csv_file_name, str (curr_num_users)], cwd="./")
                ret.wait ()
            requests.post (controller_addr + "/clear_containers")


if __name__ == "__main__":
    main ()
