import json
from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
from emission.core.get_database import url
# To support dynamic loading of client-specific libraries
import socket
import logging
import logging.config

# For decoding JWTs using the google decode URL
import requests

# Nick's additional import for managing servers
from emission.net.int_service.machine_configs import upc_port
from pymongo import MongoClient
import pymongo
import sys

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

def get_database_table(table, keys):
    Table = _get_current_db()[table]
    for key, elements in keys.items():
        # Should add checks for typing
        key_parts = key.split("\n")
        data_types = elements[0]
        assert(len(key_parts) == len(data_types))
        index_pairs = [(key_parts[i], getattr(sys.modules["pymongo"], data_types[0])) for i in range(len(key_parts))]
        is_sparse = elements[1] == "True"
        Table.create_index(index_pairs, sparse=is_sparse)
    return Table

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
  # Holds a dict mapping field name to value for a search
  elements = request.json['search_fields']
  search_fields = elements[0]
  filtered = elements[1]
  for key, value in filtered.copy().items():
      filtered[key] = value == "True"

  # Get the database
  table = get_database_table(data_type, keys)
  retrievedData = table.find(search_fields, filtered)
  should_sort = request.json['should_sort'] == "True"
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
  print(retrievedData)
  return {'data': list(retrievedData)}

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
  # Types is a list with the same entries as the data list that is the list
  # of function names used to process the data
  types = request.json['types']
  # Get the database
  table = get_database_table(data_type, keys)
  # Ignore any preprocessing
  for data in data_list:
    document = {'$set': data}
    query = {}
    for key in list(keys.keys()):
      key_parts = key.split("\n")
      for elem in key_parts:
        parts = elem.split('.')
        data_elem = data
        type_elem = types
        logging.debug("Parts are {}, data_elem is {}".format (parts, data_elem))
        for part in parts:
          data_elem = data_elem[part]
          type_elem = type_elem[part]
        type_parts = string.rsplit(".", 1)
        assert(len(type_parts) == 2)
        module_name = type_parts[0]
        func_name = parts[1]
        if module_name not in sys.modules:
            import_module(module_name)
        func = getattr(sys.modules[module_name], func_name)
        query[key] = func(data_elem)
    result = table.update(query, document, upsert=True)
    if 'err' in result and result['err'] is not None:
      logging.error("In storeData, err = %s" % result['err'])
      raise Exception()
    else:
      logging.debug("Succesfully stored user data")

@post ("/cloud/key")
def process_key():
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
