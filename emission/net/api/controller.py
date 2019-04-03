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

userclouds = dict ()

@route ("/")
def test():
    return "This is a test. Please ignore"

@post ("/usercloud")
def spawn_usercloud ():
    contents = request.json
    if contents in userclouds:
        return userclouds[contents]
    else:
        not_spawn = True
        while (not_spawn):
            # select a random port and hope it works
            port = np.random.randint (low=2000, high = (pow (2, 16) - 1))
            res = subprocess.run (['docker', 'stack', 'deploy', '-c', 'docker/docker-compose.yml', contents])
            print (res)
            if res.returncode != 0:
                continue
            res = subprocess.run (['docker', 'service', 'update', '--publish-add', '{}:8080'.format (str (port)), "{}_web-server".format (contents)])
            if res.returncode == 0:
                not_spawn = False
        output = "http://localhost:" + str (port)
        print (port)
        time.sleep (5)
        userclouds[contents] = output
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
        run(host='localhost', port=8080, debug=True)
    elif (len (sys.argv) == 2):
        run(host='localhost', port= int (sys.argv[1]), debug=True)
    else:
        sys.stderr.write ("Error too many arguments to launch known access location.\n")
