import pymongo
import requests
import socket

from emission.net.int_service.machine_configs import certificate_bundle_path, load_endpoint, count_endpoint, distinct_endpoint, insert_endpoint, delete_endpoint, update_endpoint 

def remove_user_id_from_dicts(possible_dict):
    if isinstance(possible_dict, dict):
        if "user_id" in possible_dict:
            del possible_dict["user_id"]
        for val in possible_dict.values():
            remove_user_id_from_dicts(val)


# Class used to fake a cursor
class FakeCursor:

    def __init__(self, target_address, stage_name, indices, query_dict, filter_dict, is_many):
        self.target_address = target_address
        self.stage_name = stage_name
        remove_user_id_from_dicts(indices)
        self.indices = indices
        remove_user_id_from_dicts(query_dict)
        self.query_dict = query_dict
        remove_user_id_from_dicts(filter_dict)
        self.filter_dict = filter_dict
        self.is_many = is_many
        self.limit = 0
        self.skip = 0
        self.batch_size = 0
        self.sort_fields = None
        self.sort_direction = None

    # Methods to make the fake cursor an iterable
    def __iter__(self):
        self.iter_counter = 0
        return self

    def __next__(self):
        if self.limit != 0 and self.iter_counter > self.limit:
            raise StopIteration
        else:
            # Save old cursor values for next calls
            old_skip = self.skip

            # Set the skip and batch_size to return only 1 value
            self.skip = old_skip + self.iter_counter

            # db read
            result = self.load_data()
            print(result)
            print(len(result))
            if len(result) == 0:
                raise StopIteration
            else:
                self.iter_counter += len(result)
                self.skip = old_skip
                return result

            

    def __getitem__(self, index):
        if isinstance(index, slice):
            skip = index.start
            end = index.end
            step = index.step
            if step is not None:
                raise IndexError
            elif skip is None:
                self.skip = 0
            elif skip > 0 and (end is None or skip < end):
                self.skip = skip
            else:
                raise IndexError
            if end is None:
                self.limit = 0
            else:
                self.limit = end - skip
            return self

        elif isinstance(index, int):
            if (self.limit != 0 and index >= self.limit) or (not self.is_many and index > 1):
                raise IndexError
            else:
                modified_start = self.skip
                # Save old cursor values for next calls
                old_skip = self.skip
                old_batch_size = self.batch_size

                # Set the skip and batch_size to return only 1 value
                self.skip = old_skip + index
                self.batch_size = 1 

                # db read
                result = self.load_data()
                print(result)
                elem = result[0]

                # restore the cursor value
                self.skip = old_skip
                self.batch_size = old_batch_size
                return elem
        else:
            raise pymongo.errors.InvalidOperation

    def batch_size(self, batch_size):
        self.batch_size = batch_size
        return self

    def count(self, with_limit_and_skip=False):
        # db read
        json_entries = self.get_load_data_entries()
        json_entries['with_limit_and_skip'] = with_limit_and_skip
        try:
            r = requests.post(self.target_address + count_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            return data_json['count']

    def distinct(self, key):
        # db read
        json_entries = self.get_load_data_entries()
        json_entries['distinct_key'] = key
        try:
            r = requests.post(self.target_address + distinct_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            return data_json['distinct']


    def limit(self, limit):
        self.limit = limit
        return self

    def sort(self, key_or_list, direction=None):
        self.sort_fields = key_or_list
        self.direction = direction
        return self

    def get_load_data_entries(self):
        json_entries = dict()
        json_entries['stage_name'] = self.stage_name
        json_entries['indices'] = self.indices
        json_entries['query'] = self.query_dict
        json_entries['filter'] = self.filter_dict
        json_entries['should_sort'] = self.sort_fields is not None
        json_entries['batch_size'] = self.batch_size
        json_entries['is_many'] = self.is_many
        if self.sort_fields:
            json_entries['sort_fields'] = self.sort_fields
        return json_entries

    def load_data(self):
        json_entries = self.get_load_data_entries()
        json_entries['skip'] = self.skip
        error = False
        try:
            r = requests.post(self.target_address + load_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            print(data_json)
            return data_json['data']

# Classes used to fake results from insert, update, and delete

class FakeInsertOneResult:

    def __init__(self, target_address, stage_name, indices, data_dict):
        remove_user_id_from_dicts(indices)
        remove_user_id_from_dicts(data_dict)

        # Setup the json
        json_entries = dict()
        json_entries['stage_name'] = stage_name
        json_entries['indices'] = indices
        json_entries['data'] = data_dict
        json_entries['is_many'] = False
        # Make the call to db insert one
        error = False
        try:
            r = requests.post(target_address + insert_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            # Fill in with the results of the db call
            self.acknowledged = data_json['acknowledged']
            self.inserted_id = data_json['inserted_id']

class FakeInsertManyResult:

    def __init__(self, target_address, stage_name, indices, data_dict):
        remove_user_id_from_dicts(indices)
        remove_user_id_from_dicts(data_dict)

        # Setup the json
        json_entries = dict()
        json_entries['stage_name'] = stage_name
        json_entries['indices'] = indices
        json_entries['data'] = data_dict
        json_entries['is_many'] = True
        # Make the call to db insert one
        error = False
        try:
            r = requests.post(target_address + insert_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            # Fill in with the results of the db call
            self.acknowledged = data_json['acknowledged']
            self.inserted_ids = data_json['inserted_ids']


class FakeUpdateResult:

    def __init__(self, target_address, stage_name, indices, query_dict, data_dict, is_many):
        remove_user_id_from_dicts(indices)
        remove_user_id_from_dicts(query_dict)
        remove_user_id_from_dicts(data_dict)

        # Setup the json
        json_entries = dict()
        json_entries['stage_name'] = stage_name
        json_entries['indices'] = indices
        json_entries['query'] = query_dict
        json_entries['data'] = data_dict
        json_entries['is_many'] = is_many
        # Make the call to db insert one
        error = False
        try:
            r = requests.post(target_address + update_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            # Fill in with the results of the db call
            self.acknowledged = data_json['acknowledged']
            self.matched_count = data_json['matched_count']
            self.modified_count = data_json['modified_count']
            self.raw_result = data_json['raw_result']
            self.upserted_id = data_json['upserted_id']

class FakeDeleteResult:

    def __init__(self, target_address, stage_name, indices, query_dict, is_many):
        remove_user_id_from_dicts(indices)
        remove_user_id_from_dicts(query_dict)

        # Setup the json
        json_entries = dict()
        json_entries['stage_name'] = stage_name
        json_entries['indices'] = indices
        json_entries['query'] = query_dict
        json_entries['is_many'] = is_many
        # Make the call to db insert one
        error = False
        try:
            r = requests.post(target_address + delete_endpoint, json=json_entries, timeout=600,
                    verify=certificate_bundle_path)
        except (socket.timeout) as e:
            error = True
        #Check if sucessful
        if not r.ok or error:
            error = True
        if error:
            assert(not error)
        else:
            data_json = r.json()
            # Fill in with the results of the db call
            self.acknowledged = data_json['acknowledged']
            self.deleted_count = data_json['deleted_count']
            self.raw_result = data_json['raw_result']

# Classes used to replace the db() calls
class AbstractData:
    def __init__(self, target_address, stage_name, indices):
        self.target_address = target_address
        self.stage_name = stage_name
        self.indices = indices

    def insert_many(self, data_dict_list):
        return FakeInsertManyResult(self.target_address, self.stage_name,
                self.indices, data_dict_list)

    def insert_one(self, data_dict):
        return FakeInsertOneResult(self.target_address, self.stage_name,
                self.indices, data_dict)

    def update(self, query_dict, values_dict):
        return FakeUpdateResult(self.target_address, self.stage_name,
                self.indices, query_dict, data_dict, True)
    
    def update_one(self, query_dict, values_dict):
        return FakeUpdateResult(self.target_address, self.stage_name,
                self.indices, query_dict, data_dict, False)

    def delete_many(self, query_dict):
        return FakeDeleteResult(self.target_address, self.stage_name,
                self.indices, query_dict, True)

    def delete_one(self, query_dict):
        return FakeDeleteResult(self.target_address, self.stage_name,
                self.indices, query_dict, False)

    def find(self, query_dict, filter_dict):
        return FakeCursor(self.target_address, self.stage_name,
                self.indices, query_dict, filter_dict, True)

    def find_one(self, query_dict, filter_dict):
        return FakeCursor(self.target_address, self.stage_name,
                self.indices, query_dict, filter_dict, False)

class AnalysisTimeseriesData(AbstractData):

    def __init__(self, target_address):
        indices_dict = dict()
        indices_dict["data.start_ts"] = [[pymongo.DESCENDING], True]
        indices_dict["data.end_ts"] = [[pymongo.DESCENDING], True]
        indices_dict["data.start_loc"] = [[pymongo.GEOSPHERE], True]
        indices_dict["data.end_loc"] = [[pymongo.GEOSPHERE], True]
        self.append_local_dt_indices(indices_dict, "data.start_local_dt")
        self.append_local_dt_indices(indices_dict, "data.end_local_dt")

        # places and stops
        indices_dict["data.enter_ts"] = [[pymongo.DESCENDING], True]
        indices_dict["data.exit_ts"] = [[pymongo.DESCENDING], True]
        self.append_local_dt_indices(indices_dict, "data.enter_local_dt")
        self.append_local_dt_indices(indices_dict, "data.exit_local_dt")

        indices_dict["data.location"] = [[pymongo.GEOSPHERE], True]
        indices_dict["data.duration"] = [[pymongo.DESCENDING], True]
        indices_dict["data.mode"] = [[pymongo.HASHED], True]
        indices_dict["data.section"] = [[pymongo.HASHED], True]

        # recreated location
        indices_dict["data.ts"] = [[pymongo.DESCENDING], True]
        indices_dict["data.loc"] = [[pymongo.GEOSPHERE], True]
        self.append_local_dt_indices(indices_dict, "data.local_dt") # recreated location

        super().__init__(target_address, "Stage_analysis_timeseries", indices_dict)

    def append_local_dt_indices(self, indices_dict, index_prefix):
        indices_dict["{}.year".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.month".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.day".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.hour".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.minute".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.second".format(index_prefix)] = [[pymongo.DESCENDING], True]
        indices_dict["{}.weekday".format(index_prefix)] = [[pymongo.DESCENDING], True]

class TimeseriesData(AbstractData):

    def __init__(self, target_address):
        indices_dict = dict()
        indices_dict["metadata.key"] =[[pymongo.HASHED], False]
        indices_dict['metadata.write_ts'] = [[pymongo.DESCENDING], False]
        indices_dict['data.ts'] = [[pymongo.DESCENDING], True]
        indices_dict['data.loc'] = [[pymongo.GEOSPHERE], True]
        super().__init__(target_address, "Stage_timeseries", indices_dict)

class UsercacheData(AbstractData):

    def __init__(self, target_address):
        indices_dict = dict()
        index1 = ["metadata.write_ts",
                "metadata.key"]
        index_one = "metadata.type"
        for elem in index1:
            index_one += "\n" + elem
        indices_dict[index_one] =[[pymongo.ASCENDING, pymongo.ASCENDING, pymongo.ASCENDING], False]
        indices_dict['metadata.write_ts'] = [[pymongo.DESCENDING], False]
        indices_dict['data.ts'] = [[pymongo.DESCENDING], True]
        super().__init__(target_address, "Stage_usercache", indices_dict)

### End of classes
