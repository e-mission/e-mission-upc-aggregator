import sys
import http.client
import json
import uuid
import abc
import time
import numpy as np
from multiprocessing.dummy import Pool
import requests
from scipy.optimize import minimize
import autograd.numpy as np
from autograd import grad
import csv
import time
from emission.net.int_service.machine_configs import query_endpoint, get_queriers_endpoint, get_users_endpoint

# query_file = "query.json"

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """
    @abc.abstractmethod
    def run_query(self, data):
        pass

    @abc.abstractmethod
    def generate_diff_priv_result(self, query_result, query_json):
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

    def generate_diff_priv_result(self, query_result, query_json):
        offset = query_json['offset']
        alpha = query_json['alpha']
        privacy_budget = -1 * np.log(alpha) / offset
        return query_result + np.random.laplace(scale=1.0/float(privacy_budget))

    def __repr__(self):
        return "sum"

class AE(Query):
    def __init__(self):
        self.id = uuid.uuid4()

    def run_query(self, data):
        total = 0
        for value in data:
            total += int(value)
        return total

    def generate_diff_priv_result(self, query_result, query_json):
        offset = query_json['offset']
        alpha = query_json['alpha']
        privacy_budget = -1 * np.log(alpha) / offset
        return query_result + np.random.laplace(scale=1.0/float(privacy_budget))

    def __repr__(self):
        return "ae"

class RC():
    # Uses the optimal Asymmetric Laplacian mechanism.
    def __init__(self):
        return

    def run_query(self, data):
        total = 0
        for value in data:
            total += int(value)
        return total

    def asym_sample(self, x):
        if x < (self.k**2 / (1 + self.k**2)):
            return self.true_count + (self.k / self.e) * np.log(x * (1 + self.k**2) / self.k**2)
        else:
            return self.true_count - (np.log((1 - x) * (1 + self.k**2)) / (self.k * self.e))

    # Used in solving for optimal skewness k, result is negated as we actaully want to maximize but using a minimizer.
    def asym_prob_k(self, k):
        if self.true_count < self.r_start:
            r_start = 0
            r_end = self.r_start
        elif self.true_count > self.r_end:
            r_start = self.r_end
            r_end = self.r_end + self.r_start
        else:
            r_start = self.r_start
            r_end = self.r_end
        p_left_in_bounds = (k**2 / (1 + k**2)) * (1 - np.exp(self.e*(r_start - self.true_count)/k))
        p_right_in_bounds = (1 / (1 + k**2)) * (1 - np.exp(-self.e * (r_end - self.true_count) * k))
        return -1 * (p_left_in_bounds + p_right_in_bounds)

    # Used in Newton's method, subtracting 1 - alpha to converge to 0 in Newton's method.
    def asym_prob_e(self, e):
        if self.true_count < self.r_start:
            r_start = 0
            r_end = self.r_start
        elif self.true_count > self.r_end:
            r_start = self.r_end
            r_end = self.r_end + self.r_start
        else:
            r_start = self.r_start
            r_end = self.r_end
        p_left_in_bounds = (self.k**2 / (1 + self.k**2)) * (1 - np.exp(e*(r_start - self.true_count)/self.k))
        p_right_in_bounds = (1 / (1 + self.k**2)) * (1 - np.exp(-e * (r_end - self.true_count) * self.k))
        return p_left_in_bounds + p_right_in_bounds - (1 - self.alpha)

    def dx(self, f, k):
        return abs(f(k))

    def newtons_method(self, f, e0, delta=1e-6):
        diff = self.dx(f, e0)
        grad_f = grad(f)
        while diff > delta:
            e0 = e0 - f(e0) / grad_f(e0)
            diff = self.dx(f, e0)
        return e0

    def get_asym_noise(self, query_result, query_json):
        self.r_start = query_json['r_start']
        self.r_end = query_json['r_end']
        self.alpha = query_json['alpha']
        self.true_count = query_result
        # Initial (optimal) privacy budget.
        self.e = -2 * np.log(self.alpha) / (self.r_end - self.r_start)

        k0 = np.array([1.0])
        res = minimize(self.asym_prob_k, k0, options={'maxiter': 1000})
        self.k = res.x[0]
        print("k: " + str(self.k))

        self.e = self.newtons_method(self.asym_prob_e, self.e)
        print("Updated privacy budget: " + str(self.e))

        x = np.random.uniform()
        return self.asym_sample(x)

    def generate_diff_priv_result(self, query_result, query_json):
        if query_result >= query_json['r_end'] + query_json['r_start'] or query_result == query_json['r_start'] or query_result == query_json['r_end']:
            p = np.random.uniform()
            if p < query_json['alpha']:
                return 1 # In range.
            else:
                return 0 # Not in range.
        asym_val = self.get_asym_noise(query_result, query_json)
        if asym_val > query_json['r_start'] and asym_val < query_json['r_end']:
            return 1 # In range.
        else:
            return 0 # Not in range.

    def __repr__(self):
        return "ae"

def get_user_addrs (controller_addr, num_users_lower_bound, num_users_upper_bound):
    r = requests.post(controller_addr + get_users_endpoint, json={"count": num_users_upper_bound})
    json_addrs = r.json ()
    addr_list = list (json_addrs.values ())
    print (addr_list)
    if len(addr_list) >= num_users_lower_bound:
        return addr_list
    else:
        print ("Rejected")
        return None

def launch_query_microservices (query_type, service_count, username):
    r = requests.post(controller_addr + get_queriers_endpoint + "/{}".format (query_type), json={"user": username, "count": service_count})
    json_addrs = r.json ()
    addr_list = list (json_addrs.values ())
    print (addr_list)
    if len(addr_list) == service_count:
        return addr_list
    else:
        print ("Failure to spawn enough microservice instances")
        return None


def launch_query(q, username, user_addrs, query_micro_addrs):
    pool = Pool()
    
    assert(len(user_addrs) == len(query_micro_addrs))
    query_results = []

    for i, query_addr in enumerate(query_micro_addrs):
        user_addr = user_addrs[i]
        query_results.append(pool.apply_async(requests.post, [query_addr + query_endpoint, None, {'query': q, 'user_cloud_addr': user_addr, 'agg': username}]))
    pool.close()
    pool.join()
    results = []
    [result.wait () for result in query_results]
    try:
        for result in query_results:
            curr_resp = result.get()
            print(curr_resp.text)
            curr_json_data = json.loads(curr_resp.text)
            curr_query_result = curr_json_data['query_result']
            if curr_query_result != None:
                results.append(curr_query_result)
    except:
        print (results)
        print("Async failed.")
        return
    return results

def aggregate(query_object, query_results, query_json):
    value = query_object.run_query(query_results)
    if "alpha" in query_json:
        return query_object.generate_diff_priv_result(value, query_json)
    return value

if __name__ == "__main__":
    # Inputs:
    # 1) Query q
    # 2) Controller address
    # 3) Minimum number of users required for query
    # 4) Maximum number of users to be polled
    # 5) Username/email of the analyst
    # 6) Query type
    #7) Csv results file
    query_file = sys.argv[1]
    with open (query_file, "r") as f:
        q = json.load (f)

    controller_addr = sys.argv[2]
    num_users_lower_bound = int (sys.argv[3])
    num_users_upper_bound = int (sys.argv[4])
    username = sys.argv[5]
    query_name = sys.argv[6]
    csv_file = sys.argv[7]

    query_type_mapping = {'sum' : Sum(), 'ae': AE(), 'rc': RC()}

    start = time.time()
    user_addrs = get_user_addrs( controller_addr, num_users_lower_bound, num_users_upper_bound)
    end = time.time()
    user_addr_time = end - start

    if user_addrs is not None:

        start = time.time()
        query_micro_addrs = launch_query_microservices (query_name, len (user_addrs), username)
        end = time.time()
        query_addr_time = end - start

        if query_micro_addrs is not None:

            start = time.time()
            query_results = launch_query(q, username, user_addrs, query_micro_addrs)
            end = time.time()
            query_results_time = end - start

            if not query_results:
                print("Obtaining query results failed.")
            else:
                query_object = query_type_mapping[q['query_type']]

                start = time.time()
                agg_result = aggregate(query_object, query_results, q) # FIXME
                end = time.time()
                agg_time = end - start

                if "query_correctness" in csv_file:
                    # Append query component times to results.csv.
                    row = [str(agg_result)]

                    with open(csv_file, 'a+') as csvFile:
                        writer = csv.writer(csvFile)
                        writer.writerow(row)

                    csvFile.close()

                if "time" in csv_file:
                    # Append query component times to results.csv.
                    row = [str(user_addr_time), str(query_addr_time), str(query_results_time), str(agg_time)]

                    with open(csv_file, 'a+') as csvFile:
                        writer = csv.writer(csvFile)
                        writer.writerow(row)

                    csvFile.close()
