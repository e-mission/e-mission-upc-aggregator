import abc
import numpy as np

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """
    @abc.abstractmethod
    def generate_diff_priv_cost(self, offset, alpha):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

class AE(Query):
    def __init__(self, delta_f):
        self.query_value = 0
        self.delta_f = delta_f

    def generate_diff_priv_cost(self, alpha, offset):
        return -1 * (np.log(alpha) * self.delta_f) / offset

    def __repr__(self):
        return "ae"

