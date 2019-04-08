import sys
import http.client
import json
import uuid
import abc
import numpy as np
from multiprocessing.dummy import Pool
import requests

pool = Pool(10)
query_mapping = {'sum' : Sum()}


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

def start_query(controller_addr, num_users_lower_bound):
    addr_list = requests.post(controller_addr + "/get_user_querier_addrs")
    if len(addr_list) >= num_users_lower_bound:
        return addr_list
    else:
        return "Rejected"

def launch_query(q, query_micro_addrs):
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
    # 0) Query q
    # 1) Controller address
    # 2) Minimum number of users required for query

    q = sys.argv[1]
    controller_addr = sys.argv[2]
    num_users_lower_bound = sys.argv[3]

    query_micro_addrs = start_query(controller_addr, num_users_lower_bound)

    if query_micro_addrs != "Rejected":
        query_results = launch_query(q, query_micro_addrs)
        query_object = query_mapping[q['query_type']]
        return aggregate(query_object, query_results)




