import abc
import numpy as np

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """

    def __init__(self, delta_f):
        self.delta_f = delta_f

    @abc.abstractmethod
    def __repr__(self):
        pass


class AE(Query):

    def generate_diff_priv_cost(self, alpha, offset):
        return -1 * (np.log(alpha) * self.delta_f) / offset

    def __repr__(self):
        return "ae"

    def produce_noisy_result(self, total, alpha, offset):
        priv_cost = self.generate_diff_priv_cost(alpha, offset)
        return max(total + np.random.laplace(scale=1.0/float(priv_cost)), 0)
