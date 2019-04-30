import subprocess, time

def main ():
    # First we want to spawn a the controller in a new shell
    with open ("/dev/null", "w") as f:
        subprocess.Popen (["./e-mission-py.bash", "emission/net/api/controller.py"], cwd="./", stdout=f, stderr=f)
    time.sleep (5)
    subprocess.run (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py"], cwd="./")
    subprocess.run (["./e-mission-py.bash", "emission/net/ext_service/launch_aggregator.py"], cwd="./")


if __name__ == "__main__":
    main ()