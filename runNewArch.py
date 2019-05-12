import subprocess, time
import sys
import requests
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint


controller_addr = "{}:{}".format (controller_ip, controller_port)

def main ():
    # First we want to spawn a the controller in a new shell
    num_users = [10, 50, 100, 500, 1000]
    num_trips = [10, 50, 100, 500, 1000]
    num_queries = 40
    for curr_num_users in num_users:
        for curr_num_trips in num_trips:
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(curr_num_users), str(curr_num_trips)], cwd="./")
            print ("here1")
            ret.wait ()
            print ("here2")
            for i in range (1, 11, 1):
                i = i * .1
                for _ in range(num_queries):
                    requests.post (controller_addr + "/kill_all_queriers")
                    requests.post (controller_addr + "/pause_all_clouds")
                    csv_file_name = "csvs/time_" + str(curr_num_users) + "_" + str(curr_num_trips) + "_" + str (i * 100) + ".csv"
                    ret = subprocess.Popen (["./e-mission-py.bash", "launch_aggregator.py", csv_file_name, str (curr_num_users * i)], cwd="./")
                    ret.wait ()
            requests.post (controller_addr + "/clear_containers")


if __name__ == "__main__":
    main ()
