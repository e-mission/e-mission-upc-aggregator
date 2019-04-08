import sys
import http.client
from bottle import route, run, get, post, request
import json
import uuid
import threading
import abc
import numpy as np
import sys

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """
    @abc.abstractmethod
    def run_query(self, data):
        pass

    @abc.abstractmethod
    def generate_noise(self, data):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

class Sum(Query):
    def __init__(self):
        self.id = uuid.uuid4()

    def run_query(self, data):
        #self.amount_of_noise = 0
        total = 0
        for value in data:
            total += int(value)
        return total

    def generate_noise(self, data, privacy_budget):
        sensitivity = 1
        n = len(data)
        return np.random.laplace(scale=(n * sensitivity)/float(privacy_budget))

    def __repr__(self):
        return "sum"

# @post('/add_to_result_list')
# def add_to_result_list():
#     #print(type(request))
#     #print(type(request.body))
#     #print(request.body.decode('UTF-8'))
#     #print(request.body.read())
#     data = json.loads(request.body.read().decode('UTF-8'))
#     print(data)
#     if data['response'] == 'yes':
#         controller_uuid_set = controller_uuid_map[data['controller_ip']]
#         if uuid.UUID(data['controller_uuid']) in controller_uuid_set:
#             intermediate_result_list.append(data['value'])

#             h1 = http.client.HTTPConnection(data['controller_ip'])
#             h1.request("POST", "/user_finished", json.dumps(data)) 
#             r1 = h1.getresponse()
#         else:
#             return "Invalid controller uuid"
#     print(intermediate_result_list)

#     return "Successfully added to query list"

@post('/receive_query')
def receive_query():
    user_cloud_addr = request.json['user_cloud_addr']
    query = request.json['query']
    requests.post(user_cloud_addr + "/run/aggregate", json=query)
    return "Query sent to user cloud."

@post('/receive_user_data')
def receive_user_data():
    # Complete when we know where the datastreams intereface is.
    return "Data received."

if __name__ == "__main__":
    run(host='localhost', port=80, server='cheroot')
