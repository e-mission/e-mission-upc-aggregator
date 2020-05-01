import abc

class Query(abc.ABC):
    """
    ABC is an abstract base class to define an interface for all queries
    """
    @abc.abstractmethod
    def run_query(self, data):
        pass

    @abc.abstractmethod
    def update_current_query_result(self, data):
        pass

    @abc.abstractmethod
    def get_current_query_result(self, data):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

class Sum(Query):
    def __init__(self):
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, offset, alpha):
        return -1 * np.log(alpha) / offset

    def __repr__(self):
        return "sum"

class AE(Query):
    def __init__(self):
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, offset, alpha):
        return -1 * np.log(alpha) / offset

    def __repr__(self):
        return "ae"

class RC(Query):
    def __init__(self):
        self.query_value = 0

    def run_query(self, data):
        # If there are any trip entries satisfying the time and location query, then the user count is 1, else 0.
        if len(data) > 0:
            return 1
        else:
            return 0

    def update_current_query_result(self, query_result):
        self.query_value = query_result

    def get_current_query_result(self):
        return self.query_value

    def generate_diff_priv_cost(self, r_start, r_end, alpha):
        return -1 * np.log(alpha) / ((r_end - r_start) / 2.0)

    def __repr__(self):
        return "ae"
