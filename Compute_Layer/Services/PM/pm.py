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

def get_database_table(table, keys=None):
    Table = _get_current_db()[table]
    if keys is not None:
        for key, elements in keys.items():
            # Should add checks for typing
            key_parts = key.split("\n")
            data_types = elements[0]
            assert(len(key_parts) == len(data_types))
            index_pairs = [(key_parts[i], getattr(sys.modules["pymongo"], data_types[0])) for i in range(len(key_parts))]
            is_sparse = elements[1] == "True"
            Table.create_index(index_pairs, sparse=is_sparse)
    return Table

# Helper function the returns if the value is a leaf node.
# If it is it just returns True, otherwise it calls the function
# recursively and any dictionaries holding a leaf will apply the
# func.
def apply_func_if_not_leaf(value, func):
  if isinstance(value, dict):
    for key, data in value.copy().items():
      if (apply_func_if_not_leaf(data, func)):
        value[key] = func(data)
    return False
  else:
    return True

"""
    Returns the function specified by the module and function names.
    The function name may also be a method, in which case it will be
    class.method. For generality we will assume a recursive situation.
"""
def returnSpecifiedFunction(name_components):
    # Should add a check to whitelist only data processing functions
    assert(len(name_components) == 2)
    module_name = name_components[0]
    func_name = name_components[1]
    if module_name not in sys.modules:
      import_module(module_name)
    func = sys.modules[module_name]
    func_components = func_name.split(".")
    for name in func_components:
        func = getattr(func, name)
    return func

def process_key(key, data=None, types=None):
    parts = key.split('.')
    prev_data_dict = data
    data_elem = data
    type_elem = types
    for part in parts:
      if data:
        prev_data_dict = data_elem
        data_elem = data_elem[part]
      if types:
        type_elem = type_elem[part]
    return prev_data_dict, data_elem, type_elem, parts[-1]

def setInitPrivacyBudget():
    starting_budget = 10.0 # Replace this with a sensible value.
    setPrivacyBudget(starting_budget)
    return starting_budget

def setPrivacyBudget(budget):
    table = get_database_table("privacyBudget")
    query = {"entrytype": "privacy_budget"}
    budget_dict = {"privacy_budget" : budget}
    document = {'$set': budget_dict}
    result = table.update(query, document, upsert=True)

def getPrivacyBudget():
    table = get_database_table("privacyBudget")
    search_fields = {"entrytype": "privacy_budget"}
    filtered = {"_id": "False"}
    retrievedData = table.find(search_fields, filtered)
    return list(retrievedData)


@post('/data/load')
def loadData():
  if enc_key is None:
      abort (403, "Cannot load data without a key.\n") 
  logging.debug("Called data.load")
  data_type = request.json['data_type']
  # Keys is a json dict mapping keys to [data_type, is_sparse]
  # Each key is of the form itemA.itemB.....itemZ,
  # When entry "itemA.itemB...itemZ" + "\n" + "..." should store data[itemA][itemB]...[itemZ]
  keys = request.json['keys']
  # Decode types is a list with the same entries as the query list that is the list
  # of function names used to decode the json data
  decode_types = request.json['decode_types']
  # Decode types is a list with the same entries as the data list that is the list
  # of function names used to decode the json data
  encode_types = request.json['encode_types']
  # Holds a dict mapping field name to value for a search
  elements = request.json['search_fields']
  search_fields = elements[0]
  for elem_location, value in search_fields.copy().items():
    key_parts = elem_location.split("\n")
    for elem in key_parts:
      _, _, type_elem, _ = process_key(elem, None, decode_types)
      func = returnSpecifiedFunction(type_elem)
      if apply_func_if_not_leaf(value, func):
        search_fields[elem_location] = func(value)

  filtered = elements[1]
  for key, value in filtered.copy().items():
      filtered[key] = value == "True"

  # Get the database
  logging.debug("Search fields are {}".format (search_fields))
  table = get_database_table(data_type, keys)
  retrievedData = table.find(search_fields, filtered)
  should_sort = request.json['should_sort'] == "True"
  if should_sort:
    # Holds if there is a value to sort on and if so what direction
    sort_info = request.json['sort']
    assert(len(sort_info) == 1)
    for key, value in sort_info.items():
      sort_field = key
      if value == 'True':
        sort_direction = pymongo.ASCENDING
      else:
        sort_direction = pymongo.DESCENDING
    retrievedData = retrievedData.sort(sort_field, sort_direction)
  retrievedData = list(retrievedData)
  logging.debug("Retreived data is {}".format(retrievedData))
  for item in retrievedData:
    for key in list(keys.keys()):
      key_parts = key.split("\n")
      for elem in key_parts:
        prev_data_dict, data_elem, type_elem, end = process_key(elem, item, encode_types)
        func = returnSpecifiedFunction(type_elem)
        processed_data_elem = func(data_elem)
        prev_data_dict[end] = processed_data_elem
  return {'data' : retrievedData}

@post('/data/store')
def storeData():
  if enc_key is None:
      abort (403, "Cannot store data without a key.\n") 
  logging.debug("Called data.store")
  data_type = request.json['data_type']
  # Data is the data transferred
  data_list = request.json['data']
  # Keys is a json dict mapping keys to [data_type, is_sparse]
  # Each key is of the form itemA.itemB.....itemZ,
  # When entry itemA.itemB...itemZ should store data[itemA][itemB]...[itemZ]
  keys = request.json['keys']
  # Decode types is a list with the same entries as the data list that is the list
  # of function names used to decode the json data
  decode_types = request.json['decode_types']
  # Get the database
  table = get_database_table(data_type, keys)
  # Ignore any preprocessing
  for data in data_list:
    query = {}
    for key in list(keys.keys()):
      key_parts = key.split("\n")
      for elem in key_parts:
        prev_data_dict, data_elem, type_elem, end = process_key(elem, data, decode_types)
        func = returnSpecifiedFunction(type_elem)
        processed_data_elem = func(data_elem)
        query[elem] = processed_data_elem
        prev_data_dict[end] = processed_data_elem
    logging.debug("Query is {}".format (query))
    logging.debug("Data is {}".format (data))
    document = {'$set': data}
    result = table.update(query, document, upsert=True)
    if 'err' in result and result['err'] is not None:
      logging.error("In storeData, err = %s" % result['err'])
      raise Exception()
    else:
      logging.debug("Succesfully stored user data")


# Function used to deduct from the privacy budget. Returns
# whether or not it was possible to reduce the privacy budget.
@post ("/privacy_budget")
def reduce_privacy_budget():
    budget = getPrivacyBudget()
    if len(budget) == 0:
        privacy_budget = setInitPrivacyBudget()
    else:
        return budget
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
