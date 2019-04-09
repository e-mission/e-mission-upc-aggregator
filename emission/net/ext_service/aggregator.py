import sys
import http.client
import json
import uuid
import abc
import numpy as np
from multiprocessing.dummy import Pool
import requests

pool = Pool(10)
query_mapping = {'sum' : sum}


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
    print (r.text)
    json_addrs = r.json ()
    addr_list = list (json_addrs.values ())
    print (addr_list)
    if len(addr_list) != service_count:
        return addr_list
    else:
        print ("Failure to spawn enough microservice instances")
        return None


def launch_query(q, user_addrs, query_micro_addrs):
    query_results = []
    for addr in query_micro_addrs:
        query_results.append(pool.apply_async(requests.post, [addr + "/receive_query"], {'data': q}))
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

    q = sys.argv[1]
    controller_addr = sys.argv[2]
    num_users_lower_bound = int (sys.argv[3])
    username = sys.argv[4]
    query_name = sys.argv[5]

    user_addrs = get_user_addrs( controller_addr, num_users_lower_bound)

    if user_addrs is not None:
        query_micro_addrs = launch_query_microservices (query_name, len (user_addrs), username)
        if query_micro_addrs is not None:
            query_results = launch_query(q, user_addrs, query_micro_addrs)
            query_object = query_mapping[q['query_type']]
            print (aggregate(query_object, query_results))
