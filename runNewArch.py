import subprocess, time
import sys

def main ():
    # First we want to spawn a the controller in a new shell
    #with open ("/dev/null", "w") as f:
        #subprocess.Popen (["./e-mission-py.bash", "emission/net/int_service/swarm.py"], cwd="./", stdout=f, stderr=f)
        #subprocess.Popen (["./e-mission-py.bash", "emission/net/api/controller.py"], cwd="./", stdout=f, stderr=f)
    #time.sleep (5)
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", "10", "10"], cwd="./")
    ret.wait ()
    timestamp = str(time.time())
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py", timestamp], cwd="./")


if __name__ == "__main__":
    main ()
