import subprocess, time
import sys
import requests
import json
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint

controller_addr = "{}:{}".format (controller_ip, controller_port)
print(controller_addr)

def wipe_agg_json(f):
    with open(f, "w") as jsonFile:
        json.dump({}, jsonFile)

def reset_agg_json(f):
    with open(f, "w") as jsonFile:
        json.dump({"test_analyst": 0}, jsonFile)

def main ():
    reset_agg_json("emission/simulation/known_aggs.json")
    query_files = ["experiment_queries/q1.json", "experiment_queries/q2.json"]
    num_users = 20
    num_trips = 5
    num_queries = 100
    requests.post (controller_addr + "/setup_networks")
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(num_users), str(num_trips)], cwd="./")
    ret.wait ()
    for query_file in query_files:
        csv_file_name = "csvs/policy_all_correctness_" + query_file + "_0.05_" + str(num_users) + "_" + str(num_trips) + ".csv"
        for _ in range(num_queries):
            requests.post (controller_addr + "/pause_all_queriers")
            requests.post (controller_addr + "/pause_all_clouds")
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", query_file, csv_file_name, str(num_users)], cwd="./")
            ret.wait ()
    requests.post (controller_addr + "/clear_containers")

    requests.post (controller_addr + "/setup_networks")
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(num_users / 2), str(num_trips)], cwd="./")
    ret.wait ()
    wipe_agg_json("emission/simulation/known_aggs.json")
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(num_users / 2), str(num_trips)], cwd="./")
    ret.wait ()
    for query_file in query_files:
        csv_file_name = "csvs/policy_half_correctness_" + query_file + "_0.05_" + str(num_users) + "_" + str(num_trips) + ".csv"
        for _ in range(num_queries):
            requests.post (controller_addr + "/pause_all_queriers")
            requests.post (controller_addr + "/pause_all_clouds")
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", query_file, csv_file_name, str(num_users)], cwd="./")
            ret.wait ()
    requests.post (controller_addr + "/clear_containers")
    reset_agg_json("emission/simulation/known_aggs.json")

if __name__ == "__main__":
    main ()
