import sys
import http.client
from bottle import route, run, get, post, request
import json
import uuid
import threading
import abc
import numpy as np

intermediate_result_list = []
controller_uuid_map = {}

class RequestThread(threading.Thread):
    def __init__(self, controller, enclaves_in_query, query_object, privacy_budget):
        threading.Thread.__init__(self)
        self.enclaves_in_query = enclaves_in_query
        self.controller = controller
        self.query_object = query_object
        self.privacy_budget = privacy_budget

    def run(self):
        # for controller in controllers:
        # r = requests.post('http://' + self.controller + "/request_query", data=str(self.query_object))
        h1 = http.client.HTTPConnection(self.controller)
        h1.request("POST", "/request_query", json.dumps({'query_type':str(self.query_object), 'privacy_budget':self.privacy_budget})) 
        r1 = h1.getresponse()
        # print(r.text)
        # r = json.loads(r.text)
        # for enclave in r:
        #     if enclave['response'] != 'no':
        #         self.enclaves_in_query[self.enclave] = r['Finished']

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
            # try:
            #     value = float(data[enclave])
            # except:
            #     continue
            #self.amount_of_noise += 1
        return total

    def generate_noise(self, data, privacy_budget):
        sensitivity = 1
        n = len(data)
        return np.random.laplace(scale=(n * sensitivity)/float(privacy_budget))

    def __repr__(self):
        return "sum"

class Sum(Query):
    def __init__(self):
        self.id = uuid.uuid4()

    def run_query(self, data):
        #self.amount_of_noise = 0
        total = 0
        for value in data:
            total += int(value)
            # try:
            #     value = float(data[enclave])
            # except:
            #     continue
            #self.amount_of_noise += 1
        return total

    def generate_noise(self, data, privacy_budget):
        sensitivity = 1
        n = len(data)
        return np.random.laplace(scale=(n * sensitivity)/float(privacy_budget))

    def __repr__(self):
        return "sum"

@route('/')
def test():
    return "hello"

@post('/start_query')
def start_query():
    """
    1. Ask all servers stored in file/argument if they wanna respond to query
    2. Store who wants to respond to query
    3. Run query according to the query object passed in
    4. Generate noise according to the query object passed in and add to query val
    5. Return the noise
    """
    query_mapping = {'sum' : Sum()} #TODO: Fill in query mapping from string to object
    enclaves_in_query = {}
    request_dict = json.loads(request.body.read().decode('UTF-8'))
    query_object = query_mapping[request_dict['query_type']]
    privacy_budget = str(request_dict['privacy_budget'])

    controller_map = ['128.32.37.205:2000']
    threads = []
    for controller in controller_map:
        controller_uuid_map[controller] = set()
        thread = RequestThread(controller, enclaves_in_query, query_object, privacy_budget)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    value = query_object.run_query(intermediate_result_list)
    noise = query_object.generate_noise(intermediate_result_list, privacy_budget)
    clear_intermediate_result_list()
    return str(value + noise)

@post('/add_to_result_list')
def add_to_result_list():
    print(request)
    data = json.loads(request.body.read().decode('UTF-8'))
    print(data)
    if data['response'] == 'yes':
        controller_uuid_set = controller_uuid_map[data['controller_ip']]
        if uuid.UUID(data['controller_uuid']) in controller_uuid_set:
            intermediate_result_list.append(data['value'])

            h1 = http.client.HTTPConnection(data['controller_ip'])
            h1.request("POST", "/user_finished", data['controller_uuid']) 
            r1 = h1.getresponse()
        else:
            return "Invalid controller uuid"
    print(intermediate_result_list)

    return "Successfully added to query list"

@post('/add_uuid_map')
def add_uuid_map():
    data = json.loads(request.body.read().decode('UTF-8'))
    controller_uuid_map[data['controller_ip']].add(uuid.UUID(data['controller_uuid']))

def clear_intermediate_result_list():
    global intermediate_result_list
    intermediate_result_list = []

if __name__ == "__main__":
    json_data = json.load(open("mock_data.json"))
    run(host='0.0.0.0', port=2001, server='paste') # Different port than the agg script.
