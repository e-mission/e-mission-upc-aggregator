from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
import bson
import json
import socket
import numpy as np
import emission.core.get_database as edb
import emission.storage.timeseries.geoquery as estg
import emission.storage.decorations.analysis_timeseries_queries as esda
import emission.storage.timeseries.timequery as estt
import shared_apis.queries as saq
import shared_apis.fake_mongo_types as safmt
import datetime
import pytz
from conf.machine_configs import machines_use_tls, upc_port


def convert_objectid_to_string(dict_or_list_or_item):
    if isinstance(dict_or_list_or_item, dict):
        for key, value in dict_or_list_or_item.copy().items():
            if isinstance(value, bson.ObjectId):
                dict_or_list_or_item[key] = str(value)
            else:
                convert_objectid_to_string(value)

    elif isinstance(dict_or_list_or_item, list):
        for i, value in enumerate(dict_or_list_or_item.copy()):
            if isinstance(value, bson.ObjectId):
                dict_or_list_or_item[i] = str(value)
            else:
                convert_objectid_to_string(value)

@post('/count_query')
def count_query():
    edb.pm_address = request.json['pm_address']
    # Dummy id used as a placeholder. It must be consistent for each user but
    # otherwise doesn't matter. An optimization would remove all instance of user_uuid.
    user_uuid = request.json['uuid']
    query = request.json['query']
    query_obj = saq.AE(1)
    cost = query_obj.generate_diff_priv_cost(query['alpha'], query['offset'])

    # Try and deduce from the privacy budget
    available_budget = safmt.deduct_budget(edb.pm_address, cost)
    if not available_budget:
        # Query could not complete, no budget remaining
        return {"success": False}

    start_time = query['start_ts']
    end_time = query['end_ts']
    time_query = estt.TimeQuery("data.ts", start_time, end_time)
    region = query['sel_region']
    if region is None:
        geo_query = None
    else:
        geo_query = estg.GeoQuery(["data.loc"], region)

    loc_entry_list = esda.get_entries(esda.CLEANED_LOCATION_KEY, user_uuid, 
                                    time_query=time_query, geo_query=geo_query)
    convert_objectid_to_string(loc_entry_list)
    if len(loc_entry_list) > 0:
        ret_val = 1
    else:
        ret_val = 0
    return {"success" : True, "results": ret_val}

if __name__ == '__main__':
    server_host = socket.gethostbyname(socket.gethostname())

    if machines_use_tls:
      # We support SSL and want to use it
      key_file = open('conf/net/keys.json')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=server_host, port=upc_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
    else:
      # Non SSL option for testing on localhost
      print("Running with HTTPS turned OFF - use a reverse proxy on production")
      run(host=server_host, port=upc_port, server='cheroot', debug=True)
