# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

# This is designed to be both low effort and light weight and is NOT
# robust.

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


def spawn_service(service_file, pod_file):
    # Add section to load data
    upc_service_file = request.json["service_file"]
    upc_service_config = read_config_json(upc_service_file)
    upc_pod_file = request.json["pod_file"]
    upc_pod_config = read_config_json(upc_pod_file)
    container_name, container_port = launch_unique_service(upc_service_config, 
            upc_pod_config)
    return container_name, str(container_port)


def kill(name):
    subprocess.run(["kubectl", "delete", "service", name ,"--namespace=default"])
    subprocess.run(["kubectl", "delete", "pod", name ,"--namespace=default"])

def clear_all():
    subprocess.run(["kubectl", "delete", "--all", "services" ,"--namespace=default"])
    subprocess.run(["kubectl", "delete", "--all", "pods" ,"--namespace=default"])

def create_network():
    subprocess.run (["docker", "network", "create", "emission"], cwd="./")

### Helper functions used in the kubernetes implementation. ###


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

# Takes in a json for a kubernetes configuration and modifies the label to become the
# name passed in.
def modify_label(config_json, new_label):
    config_json['metadata']['labels']['io.kompose.service'] = new_label

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
def launch_unique_service(service_config_json, pod_config_json):
        with NamedTemporaryFile("w+", dir='.') as new_service_json_file:
            with NamedTemporaryFile("w+", dir='.') as new_pod_json_file:
                service_path_name, service_name = convert_temp_name(new_service_json_file.name)
                pod_path_name, pod_name = convert_temp_name(new_pod_json_file.name)
                # Change the service name
                modify_name(service_config_json, service_name)
                # Change the pod name
                modify_name(pod_config_json, pod_name)
                # Modify the service label
                modify_label(service_config_json, service_name)
                # Modify the pod label
                modify_label(pod_config_json, service_name)
                # Dump pod file
                json.dump(pod_config_json, new_pod_json_file)
                new_pod_json_file.flush()
                while True:
                    # Port updates need to occur for each failure because they are the
                    # most likely cause
                    new_port = modify_config_port(service_config_json)
                    # Dump service file
                    json.dump(service_config_json, new_service_json_file)
                    new_service_json_file.flush()
                    try:
                        print(pod_config_json)
                        print(service_config_json)
                        print(pod_path_name)
                        # Fix to actually catch errors
                        subprocess.run (['kubectl', 'apply', '-f', '{}'.format (pod_path_name)])
                        subprocess.run (['kubectl', 'apply', '-f', '{}'.format (service_path_name)])
                        # Replace this with a check for if the external address changes
                        subprocess.run(['/bin/bash', 'kubernetes/pod_wait.sh', '{}'.format(service_name)])
                        return service_name, new_port
                    except:
                        pass

### End of kubernetes helper functions ### 
