# File dedicated to constructing a fake user profile for tracking the allowed
# algorithms. Since the algorithms are all suppose to be known hashes this
# file will be accompanied by a known_algs.json which contains a list of
# all of the known algorithms. This file will merely select a subset of the
# known algorithms to associate with a user and provide a means to ship them

import json
import numpy as np


class AlgProfile:
    # Class take constructs the "User Profile" of allowed algorithms
    # Based upon details of known_algs.json. For now known_algs.json
    # is filled with meaningless dummy values but can hopefully soon
    # be replaced with actual algorithms and their hashes soon

    # This is really just a wrapper right now for a dictionary with
    # a method for loading JSON data.
    
    # Class variable to see if we have read the file before. If so we will
    # just load it into memory once rather than do many file reads since we
    # expect the file to be large at least initially
    is_read = False
    
    # Class variable holding a mapping of algorithm/agg names to hashes
    alg_dict = None  
    agg_dict = None

    # Default location of known algorithms and aggs relative to this file
    alg_file = "emission/simulation/known_algs.json"
    agg_file = "emission/simulation/known_aggs.json"

    privacy_budget_file = "emission/simulation/priv_budget.json"
    privacy_budget = None

    # Default value for number of algorithms
    LAMBDA_ALG = 4
    
    def __init__ (self, mean=LAMBDA_ALG, default_algs=set()):
        if not AlgProfile.is_read:
            self.read_algorithms ()
            self.read_aggregators ()
            self.read_privacy_budget ()
            AlgProfile.is_read = True

        # List of allowed aggregators and algs.
        self.aggs = set()
        self.algs = dict ()

        # Aggregator to set of allowed algs, if alg not in the set then an agg doesn't have access.
        # Use this map to specify aggregator alg access when you want a unique config for a particular aggregator.
        self.agg_alg_map = dict ()
        # If an aggregator is not in the agg_alg_map, check default_algs set of algs.
        self.default_algs = default_algs

        # Samples from a poisson distribution to get how many algorithms the user should select.
        # The choice of a poisson is arbitrary and simply because it is dependent on one parameter.
        # count = round (np.random.poisson (mean))
       
        # Select up to count elements from the array
        alg_names = AlgProfile.alg_dict.keys ()
        agg_names = AlgProfile.agg_dict.keys ()
        # names_array = np.array (list (alg_names))
        # np.random.shuffle (names_array)
        # selected_names = list (names_array) [:count]
        # for name in selected_names:
        #     self.algs[name] = AlgProfile.alg_dict[name]
        for name in alg_names:
            self.algs[name] = AlgProfile.alg_dict[name]
        for name in agg_names:
            self.aggs.add(name)

        # For experiments, take out once they are done.
        for agg in self.aggs:
            for alg in alg_names:
                self.add_to_alg_map(agg, alg)

        self.privacy_budget = AlgProfile.privacy_budget

    # def to_json(self):
    #     agg_alg_list_map = {}
    #     for key in self.agg_alg_map.keys():
    #         agg_alg_list_map[key] = list(self.agg_alg_map[key])
    #     return {"aggs": list(self.aggs), "algs": self.algs, "agg_alg_map": agg_alg_list_map, "default_algs": list(self.default_algs), "privacy_budget": self.privacy_budget}

    


    # Method for initializing the data from the json of known algorithms
    def read_algorithms (self):
        with open (AlgProfile.alg_file, "r") as f:
            AlgProfile.alg_dict = json.load (f)

    # Method for initializing the data from the json of known algorithms
    def read_aggregators (self):
        with open (AlgProfile.agg_file, "r") as f:
            AlgProfile.agg_dict = json.load (f)

    def read_privacy_budget(self):
        with open (AlgProfile.privacy_budget_file, "r") as f:
            pb_data = json.load (f)
            AlgProfile.privacy_budget = pb_data['privacy_budget']
            if AlgProfile.privacy_budget == "None":
                AlgProfile.privacy_budget = None

    # Policy check method.
    def check_policies(self, agg, alg):
        if agg not in self.aggs:
            return False

        if alg not in self.algs:
            return False

        if agg in self.agg_alg_map:
            if alg not in self.agg_alg_map[agg]:
                return False
        else:
            if alg not in self.default_algs:
                return False

        return True

    # Policy modification methods.
    def add_to_aggs(self, new_agg):
        self.aggs.add(new_agg)

    def remove_from_aggs(self, remove_agg):
        self.aggs.remove(remove_agg)

    def add_to_alg_map(self, new_agg, alg):
        if new_agg not in self.agg_alg_map:
            self.agg_alg_map[new_agg] = set()
        self.agg_alg_map[new_agg].add(alg)

    def remove_from_alg_map(self, agg, alg):
        if agg not in self.agg_alg_map:
           print("Aggregator " + str(agg) + " not in the agg_alg_map.")
        else:
            self.agg_alg_map[agg].remove(alg)

    def add_to_default_algs(self, alg):
        self.default_algs.add(alg)

    def add_all_to_default_algs(self):
        alg_names = AlgProfile.alg_dict.keys ()
        for name in alg_names:
            self.default_algs.add(name)

    def remove_from_default_algs(self, alg):
        self.default_algs.remove(alg)
