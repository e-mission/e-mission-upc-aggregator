import sys
import http.client
import json
import uuid
import abc
import numpy as np
from multiprocessing.dummy import Pool
import requests

pool = Pool(10)
query_type_mapping = {'sum' : Sum()}
query_file = "query.json"

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

def get_user_addrs (controller_addr, num_users_lower_bound):
    r = requests.post(controller_addr + "/get_user_addrs")
    json_addrs = r.json ()
    addr_list = list (json_addrs.values ())
    print (addr_list)
    if len(addr_list) >= num_users_lower_bound:
        return addr_list
    else:
        print ("Rejected")
        return None

def launch_query_microservices (query_type, service_count, username):
    r = requests.post(controller_addr + "/get_querier_addrs/{}".format (query_type), json={"user": username, "count": service_count})
    json_addrs = r.json ()
    addr_list = list (json_addrs.values ())
    print (addr_list)
    if len(addr_list) == service_count:
        return addr_list
    else:
        print ("Failure to spawn enough microservice instances")
        return None


def launch_query(q, username, user_addrs, query_micro_addrs):
    assert(len(user_addrs) == len(query_micro_addrs))
    query_results = []
    for i, query_addr in enumerate(query_micro_addrs):
        user_addr = user_addrs[i]
        query_results.append(pool.apply_async(requests.post, [query_addr + "/receive_query"], {'query': q, 'user_cloud_addr': user_addr, 'agg': username}))
    return query_results

def aggregate(query_object, query_results):
    value = query_object.run_query(intermediate_result_list)
    noise = query_object.generate_noise(intermediate_result_list, privacy_budget)
    return value + noise

if __name__ == "__main__":
    # Inputs:
    # 1) Query q
    # 2) Controller address
    # 3) Minimum number of users required for query
    # 4) Username/email of the analyst
    # 5) Query type

    with open (query_file, "r") as f:
        q = json.load (f)

    controller_addr = sys.argv[1]
    num_users_lower_bound = int (sys.argv[2])
    username = sys.argv[3]
    query_name = sys.argv[4]

    user_addrs = get_user_addrs( controller_addr, num_users_lower_bound)

    if user_addrs is not None:
        query_micro_addrs = launch_query_microservices (query_name, len (user_addrs), username)
        if query_micro_addrs is not None:
            query_results = launch_query(q, username, user_addrs, query_micro_addrs)
            query_object = query_type_mapping[q['query_type']]
            print (aggregate(query_object, query_results))
