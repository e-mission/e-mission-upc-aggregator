from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from pymongo import MongoClient
import pymongo
import os
import json
import shared_apis.fake_mongo_types as safmt
import shared_apis.index_classes as saic

# Global variables used to test and swap the api being called
pm_address = None

database_name = "Stage_database"

def get_mode_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Modes", None)

def get_habitica_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_user_habitica_access", None)

def get_section_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Sections", None)

def get_trip_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Trips", None)

def get_profile_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Profiles", None)

def get_prediction_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Predictions", None)

def get_routeDistanceMatrix_db(user_id, method):
    if not os.path.exists('routeDistanceMatrices'):
        os.makedirs('routeDistanceMatrices')
    
    routeDistanceMatrix = {}
    if not os.path.exists('routeDistanceMatrices/' + user_id + '_' + method + '_routeDistanceMatrix.json'):
        data = {}
        f = open('routeDistanceMatrices/' + user_id + '_' + method + '_routeDistanceMatrix.json', 'w+')
        f.write(json.dumps({}))
        f.close()
    else:
        f = open('routeDistanceMatrices/' + user_id + '_' + method + '_routeDistanceMatrix.json', 'r')
        routeDistanceMatrix = json.loads(f.read())
    return routeDistanceMatrix

def update_routeDistanceMatrix_db(user_id, method, updatedMatrix):
    f = open('routeDistanceMatrices/' + user_id + '_' + method + '_routeDistanceMatrix.json', 'w+')
    f.write(json.dumps(updatedMatrix))
    f.close()   


def get_client_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_clients", None)

def get_routeCluster_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_routeCluster", None)

def get_groundClusters_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_groundCluster", None)

def get_uuid_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_uuids", None)

def get_client_stats_db_backup():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_client_stats", None)

def get_server_stats_db_backup():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_server_stats", None)

def get_result_stats_db_backup():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_result_stats", None)

def get_test_db():
    return safmt.AbstractCollection(pm_address, database_name, "Test_Trips", None)

def get_transit_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_Transits", None)

def get_utility_model_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_utility_models", None)

def get_alternatives_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_alternative_trips", None)

def get_perturbed_trips_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_alternative_trips", None)

def get_usercache_db():
    return saic.UsercacheCollection(pm_address, database_name)

def get_timeseries_db():
    return saic.TimeseriesCollection(pm_address, database_name)

def get_timeseries_error_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_timeseries_error", None)

def get_analysis_timeseries_db():
    """
    " Stores the results of the analysis performed on the raw timeseries
    """
    return saic.AnalysisTimeseriesCollection(pm_address, database_name)

def get_non_user_timeseries_db():
    """
    " Stores the data that is not associated with a particular user
    """
    return saic.NonUserTimeseriesCollection(pm_address, database_name)

def get_pipeline_state_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_pipeline_state", None)

def get_push_token_mapping_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_push_token_mapping", None)

def get_common_place_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_common_place", None)

def get_common_trip_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_common_trips", None)

def get_fake_trips_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_fake_trips", None)

def get_fake_sections_db():
    return safmt.AbstractCollection(pm_address, database_name, "Stage_fake_sections", None)

# Static utility method to save entries to a mongodb collection.  Single
# drop-in replacement for collection.save() now that it is deprecated in 
# pymongo 3.0. 
# https://github.com/e-mission/e-mission-server/issues/533#issuecomment-349430623
def save(db, entry):
    if '_id' in entry:
        result = db.replace_one({'_id': entry['_id']}, entry, upsert=True)
        # logging.debug("entry has id, calling with match, result = %s" % result.raw_result)
    else:
        result = db.insert_one(entry)
        # logging.debug("entry has id, calling without match, result = %s" % result.inserted_id)
