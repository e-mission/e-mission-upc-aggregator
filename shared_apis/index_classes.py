import pymongo
from shared_apis.fake_mongo_types import AbstractCollection

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
        index1 = ["metadata.type", "metadata.write_ts",
                "metadata.key"]
        index_one = "\n".join(index1)
        indices_dict[index_one] =[[pymongo.ASCENDING, pymongo.ASCENDING, pymongo.ASCENDING], False]
        indices_dict['metadata.write_ts'] = [[pymongo.DESCENDING], False]
        indices_dict['data.ts'] = [[pymongo.DESCENDING], True]
        super().__init__(target_address, "Stage_usercache", indices_dict)
