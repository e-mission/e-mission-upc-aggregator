import json
import numpy as np
from multiprocessing.dummy import Pool
from Compute_Layer.shared_resources.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
import Compute_Layer.shared_resources.bottle as bt
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


import emission.net.auth.auth as enaa
from emission.core.wrapper.user import User
import Compute_Layer.Service_Router.launcher as clsrl
from emission.net.int_service.machine_configs import controller_port, tick_period, kill_ticks

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

users = dict()

pm_name = 'PM'

ticks = 0

@post('/profile/create')
def createUserProfile():
  try:
      logging.debug("Called createUserProfile")
      userEmail = enaa._getEmail(request, auth_method)
      logging.debug("userEmail = %s" % userEmail)
      user = User.register(userEmail)
      logging.debug("Looked up user = %s" % user)
      logging.debug("Returning result %s" % {'uuid': str(user.uuid)})
      return {'uuid': str(user.uuid)}
  except ValueError as e:
      traceback.print_exc()
      abort(403, e.message)

@post ("/service_request")
def launch_service ():
    if 'user' in request.json:
       uuid = getUUID(request)
    else:
        raise HTTPError(403, "Unable to create a uuid")
    user_uuid = str (uuid)
    service_name = request.json["service"]

    if service_name in services:
        services_dict = services[service_name]
        service_file = services_dict['service_file']
        pod_file = None
        if 'pod_file' in services_dict:
            pod_file = services_dict['pod_file'] 
    else:
        raise HTTPError(403, "Request made for an unknown service")

    pm_container_name = None
    pm_address = None
    
    # Treat the PM as a special service and always launch it
    if service_name != pm_name:
        services_dict = services[pm_name]
        pm_service_file = services_dict['service_file']
        pm_pod_file = None
        if 'pod_file' in services_dict:
            pm_pod_file = services_dict['pod_file'] 
        pm_container_name, pm_address = clsrl.spawnServiceInstance (user_uuid, False,
                pm_name, pm_service_file, pm_pod_file)


    # Launch the actual container
    container_name, address = clsrl.spawnServiceInstance (user_uuid, False, 
            service_name, service_file, pod_file)
    # This value should be used to match a container contents against a user's expectations
    #request.json["hash"]
    if user_uuid not in users:
        users[user_uuid] = {}
    if [pm_container_name]:
        users[user_uuid][pm_container_name] = ticks
    users[user_uuid][container_name] = ticks
    address_list = []
    if pm_address:
       address_list.append(pm_address)
    address_list.append(address)
    return {'addresses': address_list}

@post('/get_user_addrs')
def return_container_addrs ():
    # This functionality will later be replaced with user applications and the PM.
    user_max = int (request.json['count'])
    name_list = np.array ([user for user in list (users.keys ())])
    np.random.shuffle (name_list)
    name_list = list (name_list)
    limit = min (len (name_list), user_max)
    addr_list = []
    for i in range (limit):
        name = name_list[i]
        user_instances = users[name]
        # Hardcode 1 instance per user for the experiment
        addr = list(user_instances.keys())[0]
        addr_list.append(addr)
        user_instances[addr] = ticks
    ret_dict = dict ()
    for i, addr in enumerate(addr_list):
        ret_dict[i] = addr
    return json.dumps (ret_dict)

@post('/clear_containers')
def clear_containers ():
    global users
    clsrl.clearContainers ()
    users = dict()

@post('/setup_networks')
def setup_networks ():
    clsrl.setupNetworks ()

# Container Helper functions
def get_container_names (contents):
    process = subprocess.Popen (['./bin/deploy/container_id.sh', contents], stdout=subprocess.PIPE)
    process.wait ()
    (result, error) = process.communicate ()
    return result.decode ('utf-8').split ('\n')

    return addr 
    

def tick_incr (unused1, unused2):
    global ticks
    print ("Ticking the timer")
    ticks += 1
    check_timer (users, tick_limit=kill_ticks)
    launch_timer ()


# General functions to handle timer check for running services
def check_timer (users_dict, tick_limit):
    for user in list(users_dict.values()):
        for name, starttime in user.copy().items():
            if ticks - starttime >= tick_limit:
                kill_instance (name, user)

def kill_instance (name, user_dict):
    clsrl.killInstance (name)
    del user_dict[name]

def launch_timer ():
    signal.setitimer (signal.ITIMER_REAL, tick_period)

# Auth helpers BEGIN
# This should only be used by createUserProfile since we may not have a UUID
# yet. All others should use the UUID.

def getUUID(request, inHeader=False):
    try:
        retUUID = enaa.getUUID(request, auth_method, inHeader)
        logging.debug("retUUID = %s" % retUUID)
        if retUUID is None:
           raise HTTPError(403, "token is valid, but no account found for user")
        return retUUID
    except ValueError as e:
        traceback.print_exc()
        abort(401, e.message)

# Auth helpers END

if __name__ == "__main__":
    signal.signal (signal.SIGALRM, tick_incr)
    launch_timer ()
    if len(sys.argv) != 1:
      sys.stderr.write ("Error too many arguments to launch known access location.\n")
      sys.exit(1)
    # Read the services
    with open("Compute_Layer/Service_Router/service.json", "r") as f:
        services = json.load(f)


    # Place holder for SSL that will be replaced with 443 when run in a container.
    # Not controller port is set to be an integer by an earlier code segment
    if  controller_port == 4430:
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
