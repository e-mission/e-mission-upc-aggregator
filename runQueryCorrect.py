import subprocess, time
import sys
import requests
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint

controller_addr = "{}:{}".format (controller_ip, controller_port)

def set_alpha_to_json_file(f, alpha):
    with open(f, "r") as jsonFile:
        data = json.load(jsonFile)

    data["alpha"] = alpha

    with open(f, "w") as jsonFile:
        json.dump(data, jsonFile)

def main ():
    query_files = ["query.json", "rc.json"]
    alphas = [0.01, 0.05, 0.1, 0.2]
    num_users = 50
    num_trips = 10
    num_queries = 100
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", num_users, num_trips], cwd="./")
    ret.wait ()
    for query_file in query_files:
        for alpha in alphas:
            set_alpha_to_json_file(query_file, alpha)
            for _ in range(num_queries):
                requests.post (controller_addr + "/kill_all_queriers")
                requests.post (controller_addr + "/pause_all_clouds")
                csv_file_name = "csvs/query_correctness_" + str(num_users) + "_" + str(num_trips) + ".csv"
                ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", query_file, csv_file_name, str(curr_num_users)], cwd="./")
                ret.wait ()
    requests.post (controller_addr + "/clear_containers")

if __name__ == "__main__":
    main ()
