from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
# Standard imports
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
from past.utils import old_div
import json
import numpy as np
from random import randrange
from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
import emission.net.api.bottle as bt
# To support dynamic loading of client-specific libraries
import subprocess
import sys
import os
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

# Our imports
import emission.net.api.visualize as visualize
import emission.net.api.stats as stats
import emission.net.api.usercache as usercache
import emission.net.api.timeline as timeline
import emission.net.api.metrics as metrics
import emission.net.api.pipeline as pipeline

import emission.net.auth.auth as enaa
# import emission.net.ext_service.moves.register as auth
import emission.net.ext_service.habitica.proxy as habitproxy
from emission.core.wrapper.client import Client
from emission.core.wrapper.user import User
from emission.core.get_database import get_uuid_db, get_mode_db
import emission.core.wrapper.motionactivity as ecwm
import emission.storage.timeseries.timequery as estt
import emission.storage.timeseries.tcquery as esttc
import emission.storage.timeseries.aggregate_timeseries as estag
import emission.storage.timeseries.cache_series as esdc
import emission.core.timer as ect
import emission.core.get_database as edb
import emission.net.int_service.swarm_controller as emissc

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

runningclouds = dict ()
pausedclouds = dict ()
cloudticks = dict ()
queryinstances = dict ()
queryticks = dict ()

ticks = 0
tick_limit = 4
tick_time = 300.0

@route ("/")
def test():
    return "This is a test. Please ignore"

@post ("/usercloud")
def spawn_usercloud ():
    if 'user' in request.json:
       uuid = getUUID(request)
    else:
       uuid = None #Maybe this should error
    user_uuid = str (uuid)
    if user_uuid in runningclouds:
        cloudticks[user_uuid] = ticks
        return runningclouds[user_uuid]
    elif user_uuid in pausedclouds:
        emissc.unpauseCloudInstances (user_uuid)
        addr = pausedclouds[user_uuid]
        del pausedclouds[user_uuid]
        runningclouds[user_uuid] = addr
        cloudticks[user_uuid] = ticks
        return addr 
    else:
        output = emissc.createCloudInstance (user_uuid) 
        runningclouds[user_uuid] = output
        cloudticks[user_uuid] = ticks
        return output
    
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

@post('/get_user_addrs')
def return_container_addrs ():
    addr_list = []
    for name in list (runningclouds.keys ()):
        addr_list.append (runningclouds[name])
        cloudticks[name] = ticks
    for name in list (pausedclouds.keys ())[:]:
        unpause_cloud (name, cloudticks, runningclouds, pausedclouds)
        addr_list.append (runningclouds[name])
    ret_dict = dict ()
    for i, addr in enumerate(addr_list):
        ret_dict[i] = addr
    return json.dumps (ret_dict)

@post('/get_querier_addrs/<query_type>')
def launch_queriers (query_type):
    if 'user' in request.json:
       uuid = getUUID(request)
    else:
       uuid = None #Maybe this should error
    user_uuid = str (uuid)
    querier_count = int (request.json['count'])
    addr_list = []
    for i in range (querier_count):
       addr_list.append (launch_query (query_type, i, user_uuid))
    ret_dict = dict ()
    for i, addr in enumerate(addr_list):
        ret_dict[i] = addr
    # No way to check the updates are ready. Remove later with something more accurate 
    time.sleep (20)
    return json.dumps (ret_dict)

# Container Helper functions
def get_container_names (contents):
    process = subprocess.Popen (['./bin/deploy/container_id.sh', contents], stdout=subprocess.PIPE)
    process.wait ()
    (result, error) = process.communicate ()
    return result.decode ('utf-8').split ('\n')


def launch_query (query_type, instance_number, uuid):
    # First make sure the queries are unique to the user
    name = "{}{}".format (uuid, instance_number)
    addr = emissc.createQueryInstance (name, query_type)
    queryinstances[name] = addr
    queryticks[name] = ticks
    return addr 
    

def tick_incr (unused1, unused2):
    global ticks
    print ("Ticking the timer")
    ticks += 1
    check_timer (keylist=list (cloudticks.keys ()) [:], tickdict=cloudticks, runningdict=runningclouds, pauseddict=pausedclouds, should_kill=False)
    check_timer (keylist=list (queryticks.keys ()) [:], tickdict=queryticks, runningdict=queryinstances, pauseddict=None, should_kill=True)
    launch_timer ()


# General functions to handle timer check for running service. The arguments are:
#
# A keylist. This is the a copy of the keys in the tickdict
#
# A tickdict. This is a mapping of name ---> ticktime, which is the time the service
# was last accessed. This will be checked against running ticks to check if a service
# should be shutdown.
#
# A runningdict. This is a dictionary for all currently running services of a particular
# type. Its mapping name -----> addr, where the name is the same as tickdict and the addr
# is the location at which the service is deployed.
#
# A pauseddict. If the service should be paused when run too long this should be a dictionary
# mapping name ----> addr, the same as runningdict. All of these services should be paused and
# thus constitute a destination when pausing a container. If should_kill is True this does not
# matter and can be None
#
# Should_kill. This is a boolean flag to determine if the service should be killed or paused
# when it runs too long. 
#
# For example the userclouds is a service that should be paused. Its arguments would be
# keylist = list (cloudticks.keys ()) [:]
# tickdict = cloudticks
# runningdict = runningclouds
# pauseddict = pausedclouds
# should_kill = False
#

def check_timer (keylist, tickdict, runningdict, pauseddict=None, should_kill=False):
    for name in keylist:
        starttime = tickdict[name]
        if ticks - starttime >= tick_limit:
            if should_kill:
                kill_query (name)
            else:
                pause_cloud (name, tickdict, runningdict, pauseddict)

def kill_query (name, tickdick, runningdict):
    emissc.killQueryInstance (name)
    del runningdict[name]
    del tickdict[name]

def unpause_cloud (contents, tickdict, runningdict, pauseddict):
    emissc.unpauseCloudInstances (user_uuid)
    addr = pauseddict[contents]
    del pauseddict[contents]
    runningdict[contents] = addr
    tickdict[contents] = ticks

def pause_cloud (contents, tickdict, runningdict, pauseddict):
    emissc.pauseCloudInstances (user_uuid)
    addr = runningdict[contents]
    del runningdict[contents]
    del tickdict[contents]
    pauseddict[contents] = addr

def launch_timer ():
    signal.setitimer (signal.ITIMER_REAL, tick_time)

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
    if (len (sys.argv) == 1):
        run(host='localhost', port=4040, debug=True)
    elif (len (sys.argv) == 2):
        run(host='localhost', port= int (sys.argv[1]), debug=True)
    else:
        sys.stderr.write ("Error too many arguments to launch known access location.\n")
