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
from tempfile import NamedTemporaryFile
from multiprocessing import Lock
from emission.simulation.rand_helpers import gen_random_key_string
from emission.net.int_service.machine_configs import upc_port, querier_port

cloudVarName = "PORTMAP"

### GLOBAL VARIABLES FOR KUBERNETES IMPLEMENTATION ###

# Name upc files that will need to be duplicated
upc_service_file = "kubernetes/web-server-service.json"
upc_service_config = None
upc_pod_file = "kubernetes/web-server-pod.json"
upc_pod_config = None


# Name of the query files that will need to be duplicated
query_service_file = "kubernetes/querier-service.json"
query_service_config = None
query_pod_file = "kubernetes/querier-pod.json"
query_pod_config = None

### END OF KUBERNETES IMPLEMENTATION VARIABLES ###

# Global variables for controlling if each component uses kubernetes or docker
# This is mostly for testing parts independently and eventually kubernetes should
# be adopted
upc_kubernetes = True
query_kubernetes = False

@post('/launch_querier')
def launch_querier():
    if query_kubernetes:
        pass
    else:
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
    if upc_kubernetes:
        container_name, container_port = launch_unique_service(upc_service_config)
        return container_name +"\n" + str(container_port)
    else:
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
        return uuid + "\n" + str (cloudPort)



@post('/pause')
def pause():
    if not upc_kubernetes:
        uuid = request.json['uuid'].replace ("-", "")
        containers = get_container_names (uuid)
        for name in containers:
            if name:
                res = subprocess.run (['docker', 'container', 'pause', name])


@post('/unpause')
def unpause():
    if not upc_kubernetes:
        uuid = request.json['uuid'].replace ("-", "")
        containers = get_container_names (uuid)
        for name in containers:
            if name:
                res = subprocess.run (['docker', 'container', 'unpause', name])


@post('/kill')
def kill():
    if upc_kubernetes:
        pass
    else:
        uuid = request.json['uuid'].replace ("-", "")
        containers = get_container_names (uuid)
        for name in containers:
            if name:
                res = subprocess.run (['docker', 'container', 'stop', name])
                res = subprocess.run (['docker', 'container', 'rm', name])

@post('/clear_all')
def clear_all():
    if upc_kubernetes or query_kubernetes:
        res = subprocess.run (['./teardown_docker.sh'])

@post('/create_network')
def create_network():
    if upc_kubernetes or query_kubernetes:
        ret = subprocess.run (["docker", "network", "create", "emission"], cwd="./")

# Container Helper functions
def get_container_names (name):
    if upc_kubernetes or query_kubernetes:
        process = subprocess.Popen (['./bin/deploy/container_id.sh', name], stdout=subprocess.PIPE)
        process.wait ()
        (result, error) = process.communicate ()
        return result.decode ('utf-8').split ('\n')

### Helper functions used in the kubernetes implementation. ###

# Function that must be called once to allow for upcs to be spawned at any point in the future
def initialize_upc(upc_listening_port):
    global upc_service_config, upc_pod_config
    upc_service_config = read_config_json(upc_service_file)
    set_service_internal_port(upc_service_config, upc_listening_port)
    upc_pod_config = read_config_json(upc_pod_file)
    set_pod_internal_port(upc_pod_config, upc_listening_port)

# Function that be called once to allow for queries to be spawned at any point in the future
def initialize_querier(query_listening_port):
    global query_service_config, query_pod_config
    query_service_config = read_config_json(query_service_file)
    set_service_internal_port(query_service_config, query_listening_port)
    query_pod_config = read_config_json(query_pod_file)
    set_pod_internal_port(query_pod_config, query_listening_port)


# Helper function that reads in the givenm json filename and returns 
# a dictionary of the contents
def read_config_json(json_filename):
    with open(json_filename, "r") as json_file:
        return json.load(json_file)

# Takes in a json for a kubernetes configuration and modifies the private port to be
# the given port
def set_service_internal_port(config_json, internal_port):
    config_json['spec']['ports'][0]['targetPort'] = internal_port

def set_pod_internal_port(config_json, internal_port):
    config_json['spec']['containers'][0]['ports'][0]['containerPort'] = internal_port

# Takes in a json for a kubernetes configuration and modifies the broadcasted port
# to become a randomly assigned dynamic port
def modify_config_port(config_json):
    new_port = np.random.randint (low=30000, high = 32768)
    config_json['spec']['ports'][0]['nodePort'] = new_port
    config_json['spec']['ports'][0]['port'] = new_port
    return new_port

# Takes in a json for a kubernetes configuration and modifies the name to become the
# name passed in.
def modify_name(config_json, new_name):
    config_json['metadata']['name'] = new_name


# Helper function to convert the name produced by temporary files to one accepted by
# kubectl. Also returns the path name for the file
def convert_temp_name(old_name):
    # First remove any "/" and select the last portion
    path_name = old_name.split("/")[-1]
    # Remove any _ by replacing them with -
    new_name = path_name.replace("_", "-")
    # convert all letters to lowercase
    new_name = 'a' + new_name.lower() + 'a'
    return path_name, new_name

# Takes in a configuration that represents the standard file for the system. It modifies
# the listening port to ensure it is correct, adds a random configuration port, changes the
# name and finally launches it as a service using a temporary file. It returns the temporary
# name and the port.
def launch_unique_service(config_json):
    while True:
        new_port = modify_config_port(config_json)
        with NamedTemporaryFile("w+", dir='.') as new_json_file:
            path_name, service_name = convert_temp_name(new_json_file.name)
            modify_name(config_json, service_name)
            json.dump(config_json, new_json_file)
            new_json_file.flush()
            try:
                print(config_json)
                # Fix to actually catch errors
                subprocess.run (['kubectl', 'apply', '-f', '{}'.format (path_name)])
                time.sleep(60)
                return service_name, new_port
            except:
                pass

### End of kubernetes helper functions ### 

if __name__ == "__main__":
    # Initialize the upc_config
    if upc_kubernetes:
        initialize_upc(upc_port)

    # Initialize the querier config
    if query_kubernetes:
        initialize_querier(querier_port)

    # Run this with TLS
    key_file = open('conf/net/keys.json')
    key_data = json.load(key_file)
    host_cert = key_data["host_certificate"]
    chain_cert = key_data["chain_certificate"]
    private_key = key_data["private_key"]

    run(host=socket.gethostbyname(socket.gethostname()), port=swarm_port, server='cheroot', 
            debug=True, certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
