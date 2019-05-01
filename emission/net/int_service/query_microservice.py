import sys
import http.client
from emission.net.api.bottle import route, run, get, post, request
import json
import uuid
import threading
import abc
import numpy as np
import sys
import requests

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
        self.query_value += query_result

    def get_current_query_result(self):
        return self.query_value

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
        self.query_value += query_result

    def get_current_query_result(self):
        return self.query_value

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
        self.query_value += query_result

    def get_current_query_result(self):
        return self.query_value

    def __repr__(self):
        return "ae"

@post('/receive_query')
def receive_query():
    # TODO: pass in user_cloud_addr.
    user_cloud_addr = request.json['user_cloud_addr']
    query = request.json['query']
    query_object = query_type_mapping[query['query_type']]
    agg = request.json['agg']

    # Eventually have to add a loop that collects all the streamed data packets instead of just one.
    try:
        cloud_response = requests.post(user_cloud_addr + "/run/aggregate", json={'query': query, 'agg': agg})
    except:
        return {'query_result': None}
    print("Cloud response: " + str(cloud_response))
    print("Cloud response text: " + str(cloud_response.text))
    # end_of_stream = cloud_response.json['end_of_stream']
    return receive_user_data(cloud_response, query_object)

def receive_user_data(resp, query_object):
    # Assume the response has list of ts_entries
    # curr_data_list = resp.json['phone_data']
    json_data = json.loads(resp.text)
    curr_data_list = json_data['phone_data']

    # Get the query result by running the query on the data.
    query_result = query_object.run_query(curr_data_list)
    query_object.update_current_query_result(query_result)
    print(query_object.get_current_query_result())
    return {'query_result': query_object.get_current_query_result()}

if __name__ == "__main__":
    query_type_mapping = {'sum' : Sum(), 'ae': AE(), 'rc': RC()}
    run(host='localhost', port=6500, server='cheroot')
