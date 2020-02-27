# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

# This is designed to be both low effort and light weight and is NOT
# robust.

from emission.net.api.bottle import route, run, get, post, request
import json
import socket
import subprocess
import sys
import requests
import time
import numpy as np
from emission.net.int_service.machine_configs import swarm_port
from multiprocessing import Lock
from emission.simulation.rand_helpers import gen_random_key_string
from emission.net.int_service.machine_configs import upc_port, querier_port

cloudVarName = "PORTMAP"

@post('/launch_querier')
def launch_querier():
    global ctr
    name = request.json['name'].replace ("-", "")
    query_type = request.json['query']
    not_spawn = True
    while (not_spawn):
        # select a random port and hope it works
        port = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        envVars = {cloudVarName: "{}:{}".format (port, querier_port), "ctr": gen_random_key_string ()}
        res = subprocess.run (['docker-compose', '-p', '{}'.format (name), '-f', 'docker/docker-compose-{}.yml'.format (query_type), 'up', '-d'], env=envVars)
        if res.returncode == 0:
            not_spawn = False
    return str (port)

@post('/launch_cloud')
def launch_cloud():
    global ctr
    uuid = request.json['uuid'].replace ("-", "")
    not_spawn = True
    while (not_spawn):
        # select a random port and hope it works
        cloudPort = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        envVars = {cloudVarName: "{}:{}".format (cloudPort, upc_port), "ctr": gen_random_key_string ()}
        res = subprocess.run (['docker-compose', '-p', '{}'.format (uuid), '-f', 'docker/docker-compose.yml', 'up', '-d'], env=envVars)
        if res.returncode == 0:
            not_spawn = False
    time.sleep (10)
    return str (cloudPort)



@post('/pause')
def pause():
    uuid = request.json['uuid'].replace ("-", "")
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'pause', name])


@post('/unpause')
def unpause():
    uuid = request.json['uuid'].replace ("-", "")
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'unpause', name])


@post('/kill')
def kill():
    uuid = request.json['uuid'].replace ("-", "")
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'stop', name])
            res = subprocess.run (['docker', 'container', 'rm', name])

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
    # Run this with TLS
      key_file = open('conf/net/keys.json')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=socket.gethostbyname(socket.gethostname()), port=swarm_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
