import json
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile

# Name upc files that will need to be duplicated
upc_service_file = "web-server-service.json"
upc_service_config = None
upc_pod_file = "web-server-pod.json"
upc_pod_config = None

# Name of the query files that will need to be duplicated
query_service_file = "query-service.json"
query_service_config = None
query_pod_file = "query-pod.json"
query_pod_config = None

# Function that must be called once to allow for upcs to be spawned at any point in the future
def initialize_upc():
    global upc_service_config, upc_pod_config
    upc_service_config = read_config_json(upc_service_file)
    upc_pod_config = read_config_json(upc_pod_file)

# Function that be called once to allow for queries to be spawned at any point in the future
def initialize_queries():
    global query_service_config, query_pod_config
    query_service_config = read_config_json(query_service_file)
    query_pod_config = read_config_json(query_pod_file)


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
    config_json['spec']['ports'][0]['targetPort'] = internal_port

# Takes in a json for a kubernetes configuration and modifies the broadcasted port
# to become a randomly assigned dynamic port
def modify_config_port(config_json):
    new_port = np.random.randint (low=30000, high = 32768)
    config_json['spec']['ports'][0]['port'] = new_port

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
# name.
def launch_unique_service(config_json, server_port):
    name = None
    set_internal_port(config_json, server_port)
    # Return when success is reached
    while True:
        modify_config_port(config_json)
        with NamedTemporaryFile("w+", dir='.') as new_json_file:
            path_name, service_name = convert_temp_name(new_json_file.name)
            modify_name(config_json, service_name)
            json.dump(config_json, new_json_file)
            new_json_file.flush()
            subprocess.run (['kubectl', 'apply', '-f', '{}'.format (path_name)])
            return service_name

