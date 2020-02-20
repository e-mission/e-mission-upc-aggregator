import socket
import subprocess
import sys
from emission.net.int_service.machine_configs import controller_port, controller_ip

cloudVarName = "PORTMAP"

process = None

def main():
    global process
    if "http://" + socket.gethostbyname(socket.gethostname()) == controller_ip:
        ret = subprocess.Popen (["docker", "network", "create", "emission"], cwd="./")
        ret.wait ()
        envVars = {cloudVarName: "{}:{}".format (controller_port, controller_port), "ctr": "00"}
        #ret = subprocess.Popen (["docker-compose", "-f", "docker/docker-compose-controller.yml", "up", "-d"], cwd="./", env=envVars)
        #ret.wait ()
    process = subprocess.Popen (["./e-mission-py.bash", "emission/net/int_service/swarm.py"], cwd="./")
    process.wait ()


if __name__ == "__main__":
    main ()
