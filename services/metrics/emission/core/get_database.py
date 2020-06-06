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

def get_usercache_db():
    return saic.UsercacheCollection(pm_address)

def get_timeseries_db():
    return saic.TimeseriesCollection(pm_address)

def get_analysis_timeseries_db():
    """
    " Stores the results of the analysis performed on the raw timeseries
    """
    return saic.AnalysisTimeseriesCollection(pm_address)


def get_pipeline_state_db():
    return safmt.AbstractCollection(pm_address, "Stage_database", dict())

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
