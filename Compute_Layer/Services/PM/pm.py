import json
from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
from emission.core.get_database import url
# To support dynamic loading of client-specific libraries
import socket
import logging
import logging.config

import requests

# Nick's additional import for managing servers
from emission.net.int_service.machine_configs import upc_port
from pymongo import MongoClient
import pymongo
import sys
from importlib import import_module

from bson import ObjectId

# Taken from https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

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

enc_key = None
mongoHostPort = 27017
_current_db = None

def _get_current_db():
    global _current_db
    if _current_db is None:
        print("Connecting to database URL "+url)
        _current_db = MongoClient(host=url, port=mongoHostPort).Stage_database
    return _current_db

def get_collection(stage_name, indices=None):
    collection = _get_current_db()[stage_name]
    if indices is not None:
        for index, elements in indices.items():
            # Should add checks for typing
            index_parts = index.split("\n")
            data_types = elements[0]
            assert(len(index_parts) == len(data_types))
            index_pairs = [(index_parts[i], data_types[0]) for i in range(len(index_parts))]
            is_sparse = elements[1]
            collection.create_index(index_pairs, sparse=is_sparse)
    return collection

def setInitPrivacyBudget():
    starting_budget = 10.0 # Replace this with a sensible value.
    setPrivacyBudget(starting_budget)
    return starting_budget

def setPrivacyBudget(budget):
    table = get_collection("privacyBudget")
    budget_dict = {"privacy_budget" : budget}
    result = table.insert_one(budget)

def getPrivacyBudget():
    table = get_collection("privacyBudget")
    search_fields = {"entrytype": "privacy_budget"}
    filtered = {"_id": False}
    retrievedData = table.find_one(search_fields, filtered)
    datalist = list(retrievedData)
    if len(datalist) == 0:
        return None
    else:
        logging.debug("PB load is {}".format(datalist[0]))
        return datalist[0]["privacy_budget"]

# TODO add support optional parameters
def getCursor():
  stage_name = request.json['stage_name']
  # query is the filter
  query = request.json['query']
  filter_dict = request.json['filter']
  # Indices is a json dict mapping keys to [data_type, is_sparse]
  # Each index is of the form itemA.itemB.....itemZ,
  indices = request.json['indices']
  is_many = request.json['is_many']
  should_sort = request.json['should_sort']
  limit = request.json['limit']
  skip = request.json['skip']

  db = get_collection(stage_name, indices)
  if is_many:
    cursor = db.find(query, filter_dict)
  else:
    cursor = db.find_one(query, filter_dict)

  should_sort = request.json['should_sort'] == "True"
  if should_sort:
    sort_info = request.json['sort']
    cursor.sort(sort_info)
  cursor.skip(skip)
  cursor.limit(limit)
  return cursor

@post('/data/find')
def findData():
  if enc_key is None:
      abort (403, "Cannot load data without a key.\n") 
  cursor = getCursor()
  data = list(getCursor())
  result_dict = {'data' : data}
  return JSONEncoder().encode(result_dict)

@post('/data/count')
def countData():
  if enc_key is None:
      abort (403, "Cannot load data without a key.\n")
  cursor = getCursor()
  with_limit_and_skip = request.json['with_limit_and_skip']
  return {'count' : cursor.count(with_limit_and_skip)}

@post('/data/distinct')
def distinctData():
  if enc_key is None:
      abort (403, "Cannot load data without a key.\n")
  cursor = getCursor()
  distinct_key = request.json['distinct_key']
  return {'distinct' : cursor.distinct(distinct_key)}

# TODO Handle optional parameters
@post('/data/insert')
def insertData():
  if enc_key is None:
      abort (403, "Cannot store data without a key.\n") 
  stage_name = request.json['stage_name']
  # Data is the data transferred
  data = request.json['data']
  # Indices is a json dict mapping keys to [data_type, is_sparse]
  # Each index is of the form itemA.itemB.....itemZ,
  indices = request.json['indices']
  is_many = request.json['is_many']
  # Get the database
  db = get_collection(stage_name, indices)
  result_dict = dict()
  if is_many:
    result = db.insert_many(data)
    result_dict['inserted_ids'] = result.inserted_ids
  else:
    result = db.insert_one(data)
    result_dict['inserted_id'] = result.inserted_id
  result_dict['acknowledged'] = result.acknowledged
  return JSONEncoder().encode(result_dict)

# TODO Handle optional parameters
@post('/data/update')
def updateData():
  if enc_key is None:
      abort (403, "Cannot store data without a key.\n") 
  stage_name = request.json['stage_name']
  # query is the filter
  query = request.json['query']
  # Data is the data transferred
  data = request.json['data']
  # Indices is a json dict mapping keys to [data_type, is_sparse]
  # Each index is of the form itemA.itemB.....itemZ,
  indices = request.json['indices']
  is_many = request.json['is_many']
  # Get the database
  db = get_collection(stage_name, indices)
  if is_many:
    result = db.update_many(query, data)
  else:
    result = db.update_one(query, data)
  result_dict = dict()
  result_dict['acknowledged'] = result.acknowledged
  result_dict['matched_count'] = result.matched_count
  result_dict['modified_count'] = result.modified_count
  result_dict['raw_result'] = result.raw_result
  result_dict['upserted_id'] = result.upserted_id
  return JSONEncoder().encode(result_dict)

# TODO Handle optional parameters
@post('/data/delete')
def deleteData():
  if enc_key is None:
      abort (403, "Cannot store data without a key.\n") 
  stage_name = request.json['stage_name']
  # query is the filter
  query = request.json['query']
  # Indices is a json dict mapping keys to [data_type, is_sparse]
  # Each index is of the form itemA.itemB.....itemZ,
  indices = request.json['indices']
  is_many = request.json['is_many']
  # Get the database
  db = get_collection(stage_name, indices)
  if is_many:
    result = db.delete_many(query, data)
  else:
    result = db.delete_one(query, data)
  result_dict = dict()
  result_dict['acknowledged'] = result.acknowledged
  result_dict['deleted_count'] = result.deleted_count
  result_dict['raw_result'] = result.raw_result
  return JSONEncoder().encode(result_dict)

# Function used to deduct from the privacy budget. Returns
# whether or not it was possible to reduce the privacy budget.
@post ("/privacy_budget")
def reduce_privacy_budget():
    budget = getPrivacyBudget()
    if budget is None:
        privacy_budget = setInitPrivacyBudget()
    else:
        privacy_budget = float(budget)
    cost = float(request.json['cost'])
    # Remove returning the budget after testing
    if privacy_budget - cost < 0:
        return {"success": False, "budget" : ""}
    else:
        privacy_budget -= cost
        setPrivacyBudget(privacy_budget)
        return {"success": True, "budget" : privacy_budget}


@post ("/cloud/key")
def add_encrypt_key():
    global enc_key
    if enc_key:
        abort (403, "Key already given\n")
    else:
        enc_key = request.json
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((url, 27018))
            s.sendall (enc_key.to_bytes (32, byteorder='big'))
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
