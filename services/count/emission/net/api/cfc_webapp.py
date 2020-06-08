from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response

import json
import socket
import numpy as np
import emission.core.get_database as edb
import shared_apis.queries as saq
import shared_apis.fake_mongo_types as safmt
import datetime
import pytz
from conf.machine_configs import machines_use_tls, upc_port



@post('/count_query')
def count_query():
    edb.pm_address = request.json['pm_address']
    # Dummy id used as a placeholder. It must be consistent for each user but
    # otherwise doesn't matter. An optimization would remove all instance of user_uuid.
    user_uuid = request.json['uuid']
    query = query['query_type']
    if query['query_type'] == 'ae':
        query_obj = saq.AE(delta_f)
        cost = query_obj.generate_diff_priv_cost(query['alpha'], query['offset'])
    elif query['query_type'] =='rc':
        query_obj = saq.RC(delta_f)
        cost = query_obj.generate_diff_priv_cost(query['alpha'], query['r_end'], query['r_start'])

    # Try and deduce from the privacy budget
    available_budget = safmt.deduct_budget(edb.pm_address, cost)
    if not available_budget:
        # Query could not complete, no budget remaining
        return {"success": False}

    start_time = query['start_ts']
    end_time = query['end_ts']
    time_query = estt.TimeQuery("metadata.write_ts", start_time, end_time)
    region = query['sel_region']
    if region is None:
        geo_query = None
    else:
        geo_query = estg.GeoQuery(["data.loc"], region)

    loc_entry_list = esda.get_entries(esda.CLEANED_LOCATION_KEY, user_uuid, 
                                    time_query=time_query, geo_query=geo_query)

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
