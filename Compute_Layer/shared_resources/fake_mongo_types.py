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
        self._limit = 0
        self._skip = 0
        self._batch_size = 0
        self._sort_fields = None
        self._sort_direction = None
        self._stored_data = []
        self.array_offset = 0

    # Methods to make the fake cursor an iterable
    def __iter__(self):
        self.iter_counter = 0
        self.array_offset = 0
        self._stored_data = []
        return self

    def __next__(self):
        if self._limit != 0 and self.iter_counter > self._limit:
            raise StopIteration
        else:
            array_index = self.iter_counter - self.array_offset
            if array_index >= len(self._stored_data):
                # Save old cursor values for next calls
                old_skip = self._skip

                # Set the skip and batch_size to return only 1 value
                self._skip = old_skip + self.iter_counter

                # db read
                self.array_offset += len(self._stored_data)
                array_index -= len(self._stored_data)
                self._stored_data = self.load_data()
                if not self.is_many:
                    self._stored_data = [self._stored_data]
                print(len(self._stored_data))
                if len(self._stored_data) == 0:
                    raise StopIteration
                else:
                    self._skip = old_skip
            self.iter_counter += 1
            return self._stored_data[array_index] 

            

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
                self._limit = end - skip
            return self

        elif isinstance(index, int):
            if (self._limit != 0 and index >= self._limit) or (not self.is_many and index > 1):
                raise IndexError
            else:
                array_index = self.iter_counter - self.array_offset
                if array_index >= len(self._stored_data) or array_index < 0:
                    # Save old cursor values for next calls
                    old_skip = self._skip

                    # Set the skip and batch_size to return only 1 value
                    self._skip = old_skip + index
                    self.has_many = False

                    # db read
                    result = self.load_data()
                    if not self.many:
                        result = [result]
                    new_offset = self._skip
                    # restore the cursor value
                    self._skip = old_skip
                    self.has_many = old_has_many
                    if len(result) == 0:
                        raise IndexError
                    else:
                        self._store_data = result
                        self.array_offset = self._skip
                        return result[0]
        else:
            raise pymongo.errors.InvalidOperation

    def batch_size(self, batch_size):
        self._batch_size = batch_size
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
        self._limit = limit
        return self

    def sort(self, key_or_list, direction=None):
        self.sort_fields = key_or_list
        self.sort_direction = direction
        return self

    def get_load_data_entries(self):
        json_entries = dict()
        json_entries['stage_name'] = self.stage_name
        json_entries['indices'] = self.indices
        json_entries['query'] = self.query_dict
        json_entries['filter'] = self.filter_dict
        json_entries['should_sort'] = self.sort_fields is not None
        json_entries['limit'] = self._batch_size
        json_entries['is_many'] = self.is_many
        if self.sort_fields:
            json_entries['sort_fields'] = self.sort_fields
            json_entries['sort_direction'] = self.sort_direction
        return json_entries

    def load_data(self):
        json_entries = self.get_load_data_entries()
        json_entries['skip'] = self._skip
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
class AbstractCollection:
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

    def update_many(self, query_dict, data_dict):
        return FakeUpdateResult(self.target_address, self.stage_name,
                self.indices, query_dict, data_dict, True)
    
    def update_one(self, query_dict, data_dict):
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

class AnalysisTimeseriesCollection(AbstractCollection):

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

class TimeseriesCollection(AbstractCollection):

    def __init__(self, target_address):
        indices_dict = dict()
        indices_dict["metadata.key"] =[[pymongo.HASHED], False]
        indices_dict['metadata.write_ts'] = [[pymongo.DESCENDING], False]
        indices_dict['data.ts'] = [[pymongo.DESCENDING], True]
        indices_dict['data.loc'] = [[pymongo.GEOSPHERE], True]
        super().__init__(target_address, "Stage_timeseries", indices_dict)

class UsercacheCollection(AbstractCollection):

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
