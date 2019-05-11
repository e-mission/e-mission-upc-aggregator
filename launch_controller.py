import subprocess
import sys
from emission.net.int_service.machine_configs import controller_port

cloudVarName = "PORTMAP"

def main():
    envVars = {cloudVarName: "{}:{}".format (controller_port, controller_port)}
    ret = subprocess.Popen (["docker-compose", "-f", "docker/docker-compose-controller.yml", "up", "-d"], cwd="./", env=envVars)
    ret.wait ()

if __name__ == "__main__":
    main ()
