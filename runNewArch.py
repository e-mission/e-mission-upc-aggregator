import subprocess, time
import sys

def main ():
    # First we want to spawn a the controller in a new shell
    #with open ("/dev/null", "w") as f:
        #subprocess.Popen (["./e-mission-py.bash", "emission/net/int_service/swarm.py"], cwd="./", stdout=f, stderr=f)
        #subprocess.Popen (["./e-mission-py.bash", "emission/net/api/controller.py"], cwd="./", stdout=f, stderr=f)
    #time.sleep (5)
    num_users = [10, 50, 100, 500, 1000]
    num_trips = [10, 50, 100, 500, 1000]
    num_queries = 40
    for curr_num_users in num_users:
        for curr_num_trips in num_trips:
            ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", str(curr_num_users), str(curr_num_trips)], cwd="./")
            ret.wait ()

            for _ in range(num_queries):
                csv_file_name = "csvs/time_" + str(curr_num_users) + "_" str(curr_num_trips) + ".csv"
                ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", csv_file_name], cwd="./")


if __name__ == "__main__":
    main ()
