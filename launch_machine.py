import socket
import subprocess
import sys
from emission.net.int_service.machine_configs import controller_port, controller_ip

cloudVarName = "PORTMAP"

def main():
    if "http://" + socket.gethostbyname(socket.gethostname()) == controller_ip:
        envVars = {cloudVarName: "{}:{}".format (controller_port, controller_port)}
        ret = subprocess.Popen (["docker-compose", "-f", "docker/docker-compose-controller.yml", "up", "-d"], cwd="./", env=envVars)
        ret.wait ()
    else:
        print ("hello")
    subprocess.Popen (["./e-mission-py.bash", "emission/net/int_service/swarm.py"], cwd="./")


if __name__ == "__main__":
    main ()
