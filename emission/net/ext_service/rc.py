import numpy as np
import json
from scipy.optimize import minimize
import autograd.numpy as np
from autograd import grad


class RC():
    # Uses the optimal Asymmetric Laplacian mechanism.
    def __init__(self, r_start, r_end):
        self.r_start = r_start
        self.r_stop = r_end

    def run_query(self, data):
        total = 0
        for value in data:
            total += int(value)
        return total

    def asym_sample(x):
        if x < (self.k**2 / (1 + self.k**2)):
            return self.true_count + (self.k / self.e) * np.log(x * (1 + self.k**2) / self.k**2)
        else:
            return self.true_count - (np.log((1 - x) * (1 + self.k**2)) / (self.k * self.e))

    # Used in solving for optimal skewness k, result is negated as we actaully want to maximize but using a minimizer.
    def asym_prob_k(k):
        p_left_in_bounds = (k**2 / (1 + k**2)) * (1 - np.exp(self.e*(self.r_start - self.true_count)/k))
        p_right_in_bounds = (1 / (1 + k**2)) * (1 - np.exp(-self.e * (self.r_stop - self.true_count) * k))
        return -1 * (p_left_in_bounds + p_right_in_bounds)

    # Used in Newton's method, subtracting 1 - alpha to converge to 0 in Newton's method.
    def asym_prob_e(e):
        p_left_in_bounds = (k**2 / (1 + k**2)) * (1 - np.exp(self.e*(self.r_start - self.true_count)/k))
        p_right_in_bounds = (1 / (1 + k**2)) * (1 - np.exp(-self.e * (self.r_stop - self.true_count) * k))
        return p_left_in_bounds + p_right_in_bounds - (1 - self.alpha)

    def newtons_method(f, e0, delta=1e-8):
        diff = dx(f, e0)
        grad_f = grad(f)
        while diff > delta:
            #print("Diff " + str(diff))
            grad_f(e0)
            e0 = e0 - f(e0) / grad_f(e0)
            #print("E " + str(e0))
            diff = dx(f, e0)
        #print('Root is at: ', e0)
        #print('f(e) at root is: ', f(e0))
        return e0

    def get_asym_noise(query_result, query_json):
        self.r_start = query_json['r_start']
        self.r_end = query_json['r_end']
        self.alpha = query_json['alpha']
        self.true_count = query_result
        # Initial (optimal) privacy budget.
        self.e = -2 * np.log(self.alpha) / (self.r_stop - self.r_start)

        k0 = np.array([1.0])
        res = minimize(asym_prob_k, k0, options={'xtol': 1e-8})
        self.k = res.x[0]
        print(self.k)

        self.e = newtons_method(asym_prob_e, self.e)
        print("Updated privacy budget: " + str(self.e))

        x = np.random.uniform()
        return asym_sample(x)

    def generate_noise(self, query_result, query_json):
        return asym_sample(query_result, query_json)

    def __repr__(self):
        return "ae"


with open ("rc.json", "r") as f:
    query = json.load (f)
    print(query)

query_type_mapping = {'rc': RC()}

query_results = []
for _ in range(55):
    query_results.append(1.0)

rc_query_object = query_type_mapping[q['query_type']]

true_count = rc_query_object.run_query(query_results)
print("True count: " + str(true_count))

noisy_count = query_object.generate_noise(true_count, query_json)
print(noisy_count)

if noisy_count > rc_query_object.r_start and noisy_count < rc_query_object.r_end:
    print("In range")
else:
    print("NOT in range")
