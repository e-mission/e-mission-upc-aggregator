# This file is meant as a replacement for cluster coordination when running in
# docker directly. One server needs to be launched on each machine in use, all
# must be accessible from the service router's machine, and the IP addresses of
# each machine must be added to the configuration file. This should not be
# considered an attempt at an optimal coordination between machines.

from emission.net.api.bottle import route, run, get, post, request
import json
import socket
import subprocess
import sys
import requests
import numpy as np
from emission.net.int_service.machine_configs import swarm_port
from tempfile import NamedTemporaryFile
from emission.simulation.rand_helpers import gen_random_key_string

cloudVarName = "PORTMAP"

# Helper function to convert the name produced by temporary files to one accepted by
# docker-compose. Also returns the path name for the file
def convert_temp_name(old_name):
    # First remove any "/" and select the last portion
    path_name = old_name.split("/")[-1]
    # Remove any _ by replacing them with -
    new_name = path_name.replace("_", "-")
    # convert all letters to lowercase
    new_name = 'a' + new_name.lower() + 'a'
    return new_name


@post('/launch_service')
def launch_service():
    compose_file = request.json['compose_file'].replace ("-", "")
    # To generate a random name we create a random file and select its name.
    # This method is not necessary but we know it works for kubernetes
    with NamedTemporaryFile("w+", dir='.') as f:
        name = convert_temp_name(f.name)
    not_spawn = True
    while (not_spawn):
        # select a random port and hope it works
        cloudPort = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        envVars = {cloudVarName: "{}:{}".format (cloudPort, upc_port), "ctr": gen_random_key_string()}
        res = subprocess.run (['docker-compose', '-p', '{}'.format (name), '-f', 
            '{}'.format(compose_file), 'up', '-d'], env=envVars)
        if res.returncode == 0:
            not_spawn = False
    json_results = dict()
    json_results['name'] = name
    json_results['port'] = cloudPort
    return json_results



@post('/pause')
def pause():
    name = request.json['name'].replace ("-", "")
    containers = get_container_names (name)
    paused = False
    for name in containers:
        if name:
            paused = True
            res = subprocess.run (['docker', 'container', 'pause', name])
    results_json = {'success': paused}
    return results_json


@post('/unpause')
def unpause():
    name = request.json['name'].replace ("-", "")
    containers = get_container_names (name)
    unpaused = False
    for name in containers:
        if name:
            unpaused = True
            res = subprocess.run (['docker', 'container', 'unpause', name])
    results_json = {'success': unpaused}
    return results_json


@post('/kill')
def kill():
    name = request.json['name'].replace ("-", "")
    containers = get_container_names (name)
    removed = False
    for name in containers:
        if name:
            removed = True
            res = subprocess.run (['docker', 'container', 'stop', name])
            res = subprocess.run (['docker', 'container', 'rm', name])
    results_json = {'success': removed}
    return results_json


@post('/clear_all')
def clear_all():
    res = subprocess.run (['./teardown_docker.sh'])

@post('/create_network')
def create_network():
    ret = subprocess.run (["docker", "network", "create", "emission"], cwd="./")

# Container Helper functions
def get_container_names (name):
    process = subprocess.Popen (['./bin/deploy/container_id.sh', name], stdout=subprocess.PIPE)
    process.wait ()
    (result, error) = process.communicate ()
    return result.decode ('utf-8').split ('\n')

if __name__ == "__main__":
    if swarm_port == 443:
      # Run this with TLS
      key_file = open('conf/net/keys.json')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=socket.gethostbyname(socket.gethostname()), port=swarm_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
    else:
      # Run this without TLS
      run(host=socket.gethostbyname(socket.gethostname()), port=swarm_port, server='cheroot', debug=True)

