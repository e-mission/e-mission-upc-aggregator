import subprocess, time
import sys
import requests
import json
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint

controller_addr = "{}:{}".format (controller_ip, controller_port)

def set_priv_budget(f, val):
    with open(f, "r") as jsonFile:
        data = json.load(jsonFile)

    data["privacy_budget"] = val

    with open(f, "w") as jsonFile:
        json.dump(data, jsonFile)

def main ():
    query_files = ["experiment_queries/q1_offset_25.json", "experiment_queries/q2_offset_25.json"]
    num_users = 100
    num_trips = 5
    num_queries = 75
    for query_file in query_files:
        set_priv_budget("emission/simulation/privacy_budget.json", 3)
        ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(num_users / 2), str(num_trips)], cwd="./")
        ret.wait ()
        set_priv_budget("emission/simulation/privacy_budget.json", 6)
        ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(num_users / 2), str(num_trips)], cwd="./")
        ret.wait ()
        csv_file_name = "csvs/pb_" + query_file + "_0.05_" + str(num_users) + "_" + str(num_trips) + ".csv"
        for _ in range(num_queries):
            requests.post (controller_addr + "/kill_all_queriers")
            requests.post (controller_addr + "/pause_all_clouds")
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", query_file, csv_file_name, str(num_users)], cwd="./")
            ret.wait ()
    requests.post (controller_addr + "/clear_containers")

if __name__ == "__main__":
    main ()
