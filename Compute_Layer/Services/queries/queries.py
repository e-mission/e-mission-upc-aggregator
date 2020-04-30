import sys
import socket
import http.client
from emission.net.api.bottle import route, run, get, post, request
import json
import uuid
import threading
import abc
import numpy as np
import sys
import requests
from emission.net.int_service.machine_configs import controller_ip, controller_port, service_endpoint, certificate_bundle_path, upc_port
import Compute_Layer.shared_resources.fake_mongo_types as clsrfmt

def privacy_budget_pass(query):
  alpha = query['alpha']
  query_type = query['query_type']
  if query_type == "ae":
    offset = query['offset']
    curr_pb = -1 * np.log(alpha) / offset
  elif query_type == "rc":
    offset = (query['r_end'] - query['r_start']) / 2
    curr_pb = -1 * np.log(alpha) / offset
  # Add a call to the PM to reduce the Privacy budget and return a response
  return True

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """
    @abc.abstractmethod
    def run_query(self, data):
        pass

    @abc.abstractmethod
    def update_current_query_result(self, data):
        pass

    @abc.abstractmethod
    def get_current_query_result(self, data):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

class Sum(Query):
    def __init__(self):
        self.id = uuid.uuid4()
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, offset, alpha):
        return -1 * np.log(alpha) / offset

    def __repr__(self):
        return "sum"

class AE(Query):
    def __init__(self):
        self.id = uuid.uuid4()
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, offset, alpha):
        return -1 * np.log(alpha) / offset

    def __repr__(self):
        return "ae"

class RC(Query):
    def __init__(self):
        self.id = uuid.uuid4()
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, offset, alpha):
        return -1 * np.log(alpha) / offset

    def __repr__(self):
        return "ae"

@post('/receive_query')
def receive_query():
    print("reached")
    pm_addr = request.json['pm_address']
    query = request.json['query']
    # TODO: pass in user_cloud_addr.
    print ("The query has begun")
    query_object = query_type_mapping[query['query_type']]
    budget_cost = query_object.generate_diff_priv_cost(float(query['offset']), float(query['alpha']))
    # Add check
    budget_deduction_results = clsrfmt.deduct_privacy(pm_addr, budget_cost)
    print(budget_deduction_results)
    legal_query = budget_deduction_results['success']
    if not legal_query:
        print("Failure 1")
        return {'query_result': ''}
    search_fields = [{"data_ts": {"$lt": query['end_ts'], "$gt": query['start_ts']}}, {"_id": "False"}]
    json_data, failure  = clsrfmt.load_usercache_data(pm_addr, search_fields)
    if failure:
        print("Failure 2")
        return {'query_result': ''}
    return receive_user_data(json_data, query_object)

def receive_user_data(json_data, query_object):
    # Assume the response has list of ts_entries
    # curr_data_list = resp.json['phone_data']
    curr_data_list = json_data['data']

    # Get the query result by running the query on the data.
    query_result = query_object.run_query(curr_data_list)
    query_object.update_current_query_result(query_result)
    print(query_object.get_current_query_result())
    return {'query_result': query_object.get_current_query_result()}

query_type_mapping = {'sum' : Sum(), 'ae': AE(), 'rc': RC()}

if __name__ == '__main__':
    try:
        webserver_log_config = json.load(open("conf/log/webserver.conf", "r"))
    except:
        webserver_log_config = json.load(open("conf/log/webserver.conf.sample", "r"))

    # To avoid config file for tests
    server_host = socket.gethostbyname(socket.gethostname())


    # The selection of SSL versus non-SSL should really be done through a config
    # option and not through editing source code, so let's make this keyed off the
    # port number
    if upc_port == 8000:
      # We support SSL and want to use it
      try:
        key_file = open('conf/net/keys.json')
      except:
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
