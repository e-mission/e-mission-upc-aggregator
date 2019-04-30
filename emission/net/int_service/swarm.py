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

cloudVarName = "PORTMAP"
mongoVarName = "MONGOMAP"

@post('/')
def test():
    print ("Connection successful")
    return "This is a test"

@post('/launch_querier')
def launch_querier():
    name = request.json['name']
    query_type = request.json['query']
    not_spawn = True
    while (not_spawn):
        # select a random port and hope it works
        port = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        envVars = {cloudVarName: "{}:{}".format (port, "8080")}
        res = subprocess.run (['docker-compose', '-p', '{}'.format (name), '-f', 'docker/docker-compose-{}.yml'.format (query_type), 'up', '-d'], env=envVars)
        if res.returncode == 0:
            not_spawn = False
    time.sleep (10)
    return str (port)

@post('/launch_cloud')
def launch_cloud():
    uuid = request.json['uuid']
    not_spawn = True
    while (not_spawn):
        # select a random port and hope it works
        cloudPort = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        mongoPort = np.random.randint (low=2000, high = (pow (2, 16) - 1))
        envVars = {cloudVarName: "{}:{}".format (cloudPort, "8080"), mongoVarName: "{}:{}".format (mongoPort, "27017")}
        res = subprocess.run (['docker-compose', '-p', '{}'.format (uuid), '-f', 'docker/docker-compose.yml', 'up', '-d'], env=envVars)
        if res.returncode == 0:
            not_spawn = False
    time.sleep (10)
    return str (cloudPort)



@post('/pause')
def pause():
    uuid = request.json['uuid']
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'pause', name])


@post('/unpause')
def unpause():
    uuid = request.json['uuid']
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'unpause', name])


@post('/kill')
def kill():
    uuid = request.json['uuid']
    containers = get_container_names (uuid)
    for name in containers:
        if name:
            res = subprocess.run (['docker', 'container', 'stop', name])
            res = subprocess.run (['docker', 'container', 'rm', name])

# Container Helper functions
def get_container_names (name):
    process = subprocess.Popen (['./bin/deploy/container_id.sh', name], stdout=subprocess.PIPE)
    process.wait ()
    (result, error) = process.communicate ()
    return result.decode ('utf-8').split ('\n')


if __name__ == "__main__":
    run(host="127.0.0.1", port=54321, server='cheroot')
