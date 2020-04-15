import socket
import subprocess
import sys
from emission.net.int_service.machine_configs import controller_port, controller_ip

cloudVarName = "PORTMAP"

def main():
    ret = subprocess.Popen (["docker", "network", "create", "emission"], cwd="./")
    ret.wait ()
    if "http://" + socket.gethostbyname(socket.gethostname()) == controller_ip:
        envVars = {cloudVarName: "{}:{}".format (controller_port, controller_port), "ctr": "00"}
        #ret = subprocess.Popen (["docker-compose", "-f", "docker/docker-compose-controller.yml", "up", "-d"], cwd="./", env=envVars)
        #ret.wait ()
    process = subprocess.Popen (["./e-mission-py.bash", "Compute_Layer/Service_Router/swarm.py"], cwd="./")
    process.wait ()


if __name__ == "__main__":
    main ()
