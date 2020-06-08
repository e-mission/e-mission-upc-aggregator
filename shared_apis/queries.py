import abc
import numpy as np

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """

    def __init__(self, delta_f):
        self.query_value = 0
        self.delta_f = delta_f

    @abc.abstractmethod
    def generate_diff_priv_cost(self, offset, alpha):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass



class AE(Query):

    def generate_diff_priv_cost(self, alpha, offset):
        return -1 * (np.log(alpha) * self.delta_f) / offset

    def __repr__(self):
        return "ae"

# Note this example hasn't been extended to general delta_f and the math
# has only been checked for the count query (delta_f = 1). Double check
# the math if you wish to use the RC query for general delta_f.
class RC(query):

    def generate_diff_priv_cost(self, alpha, r_end, r_start):
        offset = (r_end - r_start) / 2
        return -1 * (np.log(alpha) * self.delta_f) / offset

    def __repr__(self):
        return "rc"
