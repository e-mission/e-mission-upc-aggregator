import json
import numpy as np
from multiprocessing.dummy import Pool
from shared_apis.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
import shared_apis.bottle as bt
# To support dynamic loading of client-specific libraries
import subprocess
import sys
import signal
import logging
import logging.config

from datetime import datetime
import time
import arrow
from uuid import UUID
# So that we can set the socket timeout
import socket
# For decoding JWTs using the google decode URL
import urllib.request, urllib.parse, urllib.error
import requests
import traceback
import xmltodict
import urllib.request, urllib.error, urllib.parse
import bson.json_util


import service_router.launcher as srl
from emission.net.int_service.machine_configs import controller_port, upc_mode

try:
    config_file = open('conf/net/api/webserver.conf')
except:
    logging.debug("webserver not configured, falling back to sample, default configuration")
    config_file = open('conf/net/api/webserver.conf.sample')

config_data = json.load(config_file)
static_path = config_data["paths"]["static_path"]
python_path = config_data["paths"]["python_path"]
server_host = config_data["server"]["host"]
server_port = config_data["server"]["port"]
socket_timeout = config_data["server"]["timeout"]
log_base_dir = config_data["paths"]["log_base_dir"]
auth_method = config_data["server"]["auth"]

BaseRequest.MEMFILE_MAX = 1024 * 1024 * 1024 # Allow the request size to be 1G
# to accomodate large section sizes

print("Finished configuring logging for %s" % logging.getLogger())
app = app()

# List of all supported services
services = None

pods = dict()

pm_name = 'PM'

@post ("/service_request")
def request_service():
    service_name = request.json["service"]
    if service_name in services:
        services_dict = services[service_name]
        if upc_mode == "kubernetes":
            service_file = services_dict['service_file']
            pod_file = services_dict['pod_file'] 
        elif upc_mode == "docker":
            service_file = services_dict['compose_file']
            pod_file = None
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")
    else:
        raise HTTPError(403, "Request made for an unknown service")

    # Launch the actual container
    container_name, address = srl.spawnServiceInstance (service_file, pod_file)
    pods[address] = container_name
    return {'address': address}

@post('/pause')
def pause_pod():
    address = request.json["address"]
    srl.pauseInstance(pods[address])

@post('/unpause')
def resume_pod():
    address = request.json["address"]
    srl.resumeInstance(pods[address])

@post('/kill')
def kill_service_and_pod():
    address = request.json["address"]
    srl.killInstance(pods[address])
    del pods[address]

@post('/clear_containers')
def clear_containers ():
    global pods
    srl.clearContainers ()
    pods = dict()

@post('/setup_networks')
def setup_networks ():
    srl.setupNetworks ()

# Container Helper functions
def get_container_names (contents):
    process = subprocess.Popen (['./bin/deploy/container_id.sh', contents], stdout=subprocess.PIPE)
    process.wait ()
    (result, error) = process.communicate ()
    return result.decode ('utf-8').split ('\n')

    return addr 

# Auth helpers END

if __name__ == "__main__":
    if len(sys.argv) != 1:
      sys.stderr.write ("Error too many arguments to launch known access location.\n")
      sys.exit(1)
    # Read the services
    if upc_mode == "kubernetes":
        service_filename = "Compute_Layer/Service_Router/kubernetes_services.json"
    elif upc_mode == "docker":
        service_filename = "Compute_Layer/Service_Router/docker_services.json"
    else:
          sys.stderr.write ("Unknown UPC mode. Reconfigure router with either kubernetes or docker.\n")
          sys.exit(1)
    with open(service_filename, "r") as f:
        services = json.load(f)


    # Place holder for SSL that will be replaced with 443 when run in a container.
    # Not controller port is set to be an integer by an earlier code segment
    if controller_port == 443:
      # We support SSL and want to use it
      key_file = open('conf/net/keys.json')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=socket.gethostbyname(socket.gethostname()), port=controller_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
    else:
      print("Running with HTTPS turned OFF - use a reverse proxy on production")
      run(host=socket.gethostbyname(socket.gethostname()), port=controller_port, server="cheroot", debug=True)
