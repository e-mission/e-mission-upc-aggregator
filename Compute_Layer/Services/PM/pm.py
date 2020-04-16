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
import sys
import socket
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
from emission.core.get_database import get_uuid_db, get_mode_db, url
import emission.core.wrapper.motionactivity as ecwm
import emission.storage.timeseries.timequery as estt
import emission.storage.timeseries.tcquery as esttc
import emission.storage.timeseries.aggregate_timeseries as estag
import emission.storage.decorations.analysis_timeseries_queries as esda
import emission.storage.timeseries.cache_series as esdc
import emission.core.timer as ect
import emission.core.get_database as edb
import emission.storage.timeseries.geoquery as estg
import emission.simulation.profile_json as pj

# Nick's additional import for managing servers
from emission.net.int_service.machine_configs import upc_port
from pymongo import MongoClient
import pymongo

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

mongoHostPort = 27017
_current_db = None
def _get_current_db():
    global _current_db
    if _current_db is None:
        print("Connecting to database URL "+url)
        _current_db = MongoClient(host=url, port=mongoHostPort).Stage_database
    return _current_db

def get_database_table(table, keys):
    Table = _get_current_db()[table]
    for key, elements in keys.items():
        # Should add checks for typing
        data_type = getattr(pymongo, elements[0])
        is_sparse = bool(elements[1])
        Table.create_index([key, data_type], sparse=is_sparse)
    return Table

@post('/data/load')
def loadData():
  if key is None:
      abort (403, "Cannot load data without a key.\n") 
  logging.debug("Called data.load")
  user_uuid=getUUID(request)
  data_type = request.json['data_type']
  # Keys is a json dict mapping keys to [data_type, is_sparse]
  # Each key is of the form itemA.itemB.....itemZ,
  # When entry itemA.itemB...itemZ should store data[itemA][itemB]...[itemZ]
  keys = request.json['keys']
  # Holds a dict mapping field name to value for a search
  search_fields = request.json['search_fields']
  # Get the database
  table = get_database_table(data_type, keys)
  assert(len(sort_info) == 1)
  sort_field = list(sort_info.keys()
  retrievedData = table.find(search_fields)
  should_sort = bool(request.json['should_sort']
  if should_sort:
    # Holds if there is a value to sort on and if so what direction
    sort_info = request.json['sort']
    assert(len(sort_info) == 1)
    for key, value in sort_info.items():
      sort_field = key
      if bool(value):
        sort_direction = pymongo.ASCENDING
      else:
        sort_direction = pymongo.DESCENDING
    retrievedData = retrievedData.sort(sort_field, sort_direction)
  return list(retrievedData)

@post('/data/store')
def storeData():
  if key is None:
      abort (403, "Cannot store data without a key.\n") 
  logging.debug("Called data.store")
  user_uuid=getUUID(request)
  data_type = request.json['data_type']
  # Data is the data transferred
  data_list = request.json['data']
  # Keys is a json dict mapping keys to [data_type, is_sparse]
  # Each key is of the form itemA.itemB.....itemZ,
  # When entry itemA.itemB...itemZ should store data[itemA][itemB]...[itemZ]
  keys = request.json['keys']
  # Get the database
  table = get_database_table(data_type, keys)
  # Ignore any preprocessing
  for data in data_list:
    document = {'$set': data}
    query = {}
    for key in list(keys.keys()):
      parts = key.split('.')
      data_elem = data
      for part in parts:
        data_elem = data_elem[part]
      query[key] = data_elem
    result = table.update(query, document, upsert=True)
    if 'err' in result and result['err'] is not None:
      logging.error("In storeData, err = %s" % result['err'])
      raise Exception()
    else:
      logging.debug("Succesfully stored user data")


@post('/profile/create')
def createUserProfile():
  global global_uuid
  try:
      logging.debug("Called createUserProfile")
      userEmail = enaa._getEmail(request, auth_method)
      logging.debug("userEmail = %s" % userEmail)
      user = User.register(userEmail)
      logging.debug("Looked up user = %s" % user)
      logging.debug("Returning result %s" % {'uuid': str(user.uuid)})
      global_uuid = user.uuid
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

key = None
global_uuid = None

@post ("/cloud/key")
def process_key():
    global key
    if key:
        abort (403, "Key already given\n")
    else:
        key = request.json
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((url, 27018))
            s.sendall (key.to_bytes (32, byteorder='big'))
            s.recv(1024)

# TODO:
# 1. Add a generic interface for streaming data
# 2. Add differential privacy details into memory and add operations to modify
#    them.
# Future work may also include adding permission checks here.

if __name__ == '__main__':
    try:
        webserver_log_config = json.load(open("conf/log/webserver.conf", "r"))
    except:
        webserver_log_config = json.load(open("conf/log/webserver.conf.sample", "r"))

    logging.config.dictConfig(webserver_log_config)
    logging.debug("This should go to the log file")
    
    # To avoid config file for tests
    server_host = socket.gethostbyname(socket.gethostname())

    # We have see the sockets hang in practice. Let's set the socket timeout = 1
    # hour to be on the safe side, and see if it is hit.
    socket.setdefaulttimeout(float(socket_timeout))

    for plugin in app.plugins:
        if isinstance(plugin, JSONPlugin):
            print("Replaced json_dumps in plugin with the one from bson")
            plugin.json_dumps = bson.json_util.dumps

    print("Changing bt.json_loads from %s to %s" % (bt.json_loads, bson.json_util.loads))
    bt.json_loads = bson.json_util.loads

    # The selection of SSL versus non-SSL should really be done through a config
    # option and not through editing source code, so let's make this keyed off the
    # port number
    if server_port == "443":
      # We support SSL and want to use it
      try:
        key_file = open('conf/net/keys.json')
      except:
        logging.debug("certificates not configured, falling back to sample, default certificates")
        key_file = open('conf/net/keys.json.sample')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=server_host, port=upc_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
    else:
      # Non SSL option for testing on localhost
      print("Running with HTTPS turned OFF - use a reverse proxy on production")
      run(host=server_host, port=upc_port, server='cheroot', debug=True)

    # run(host="0.0.0.0", port=server_port, server='cherrypy', debug=True)
