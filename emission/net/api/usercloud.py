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
from random import randrange
from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
import emission.net.api.bottle as bt
# To support dynamic loading of client-specific libraries
import sys
import os
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

key = None
profile = None

@route ("/")
def test():
    return "This is a test. Please ignore"

@post ("/key")
def process_key():
    global key
    if key:
        abort (403, "Key already given\n")
    else:
        key = request.json
        print (key)

@post ("/profile")
def process_profile():
    global profile
    if profile:
        abort (403, "Profile already given\n")
    else:
        profile = request.json
        print (profile)
    
@get ("/status")
def check_status ():
    ret_string = ""
    if key is None:
        ret_string += "Key needs to be sent\n"
    if profile is None:
        ret_string += "Profile needs to be sent\n"
    if not ret_string:
        ret_string = "All information received\n"
    return ret_string

@post ("/run/useralg")
def run_algorithm ():
    contents = request.json
    print (contents['algorithm'])
    if key is None:
        abort (403, "Cannot load data for algorithms with no key\n") 
    if profile is None:
        abort (403, "Cannot run algorithms with a missing profile\n")
    if contents["algorithm"] in profile:
        return "Algorithm is known and allowed. Running the algorithm...\n" 
    else:
        abort (403, "Algorithm not approved in profile.\n")
        

@post ("/run/aggregate")
def run_aggregate ():
    pass

@post('/usercache/put')
def putIntoCache():
  logging.debug("Called userCache.put")
  user_uuid=getUUID(request)
  logging.debug("user_uuid %s" % user_uuid)
  from_phone = request.json['phone_to_server']
  return usercache.sync_phone_to_server(user_uuid, from_phone)

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
    if (len (sys.argv) == 1):
        run(host='localhost', port=4443, debug=True)
    elif (len (sys.argv) == 2):
        run(host='localhost', port= int (sys.argv[1]), debug=True)
    else:
        sys.stderr.write ("Error too many arguments to launch user cloud.\n")
