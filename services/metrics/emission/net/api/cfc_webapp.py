from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response

import json
import logging
import logging.config
import socket
import numpy as np
import emission.net.api.metrics as metrics
import emission.core.get_database as edb
import shared_apis.queries as saq
import shared_apis.fake_mongo_types as safmt
import datetime
import pytz
from conf.machine_configs import machines_use_tls, upc_port

# Dictionary of delta_f values used for adding noise to the data.
# All of these are very conservative and applied in whole day estimates.
# Further research can likely greatly reduce these numbers, especially
# when multiple days are involved
delta_f_dict = {
        # Units of trips/day
        "count": {"car" : 55, "walk" : 55, "bicycle" : 55, "transit" : 55},
        # Units of meters/day
        "distance": {"car" : 3840000, "walk" : 504000, "bicycle" : 648000, "transit" : 1440000},
        # Units of seconds/day
        "duration": {"car" : 86400, "walk" : 86400, "bicycle" : 86400, "transit" : 86400}
        }

# Helper function to convert all numpy types to python types
def numpy_to_py(dict_or_list):
    if isinstance(dict_or_list, dict):
        for key, value in dict_or_list.copy().items():
            if isinstance(value, np.integer):
                dict_or_list[key] = int(value)
            elif isinstance(value, np.floating):
                dict_or_list[key] = float(value)
            elif isinstance(value, np.ndarray):
                dict_or_list[key] = value.tolist()
            numpy_to_py(dict_or_list[key])
    elif isinstance(dict_or_list, list):
        for i, value in enumerate(dict_or_list.copy()):
            if isinstance(value, np.integer):
                dict_or_list[i] = int(value)
            elif isinstance(value, np.floating):
                dict_or_list[i] = float(value)
            elif isinstance(value, np.ndarray):
                dict_or_list[i] = value.tolist()
            numpy_to_py(dict_or_list[i])



# We assume that date times only consist of at most year, month, day, and tz.
# if month and day are not provided we will assume they represent 1 each, if only
# day is not provided we will assume it represents 1.
def extractDatetimeFromDict(datetime_dict):
    year = datetime_dict['year']
    if "month" in datetime_dict:
        month = datetime_dict['month']
        if 'day' in datetime_dict:
            day = datetime_dict['day']
        else:
            day = 1
    else:
        month = 1
        day = 1
    timezone = pytz.timezone(datetime_dict['timezone'])
    return datetime.datetime(year, month, day, tzinfo = timezone)


@post('/metrics/local_date')
def summarize_metrics():
    edb.pm_address = request.json['pm_address']
    # Dummy id used as a placeholder. It must be consistent for each user but
    # otherwise doesn't matter. An optimization would remove all instance of user_uuid.
    user_uuid = request.json['uuid']
    start_time = request.json['start_time']
    end_time = request.json['end_time']
    freq_name = request.json['freq']
    metric = request.json['metric']
    offset_dict = request.json['offset']
    alpha_dict = request.json['alpha']

    # Calculate the range of time in hours. We currently only support values in datetime.
    end_datetime = extractDatetimeFromDict(end_time)
    start_datetime = extractDatetimeFromDict(start_time)
    num_days = ((end_datetime - start_datetime).total_seconds() / 86400.0)

    cost = 0
    # We currently assume that all modes of transportation that are supported
    # through fake data are returned. We also assume the cost must be applied to each
    # metric. If you want to filter a subset or change this assumption, it should be
    # done here. That might be especially useful if you have much more car data than
    # any other type of data for example.

    delta_f_vals = delta_f_dict[metric]
    for mode, val in delta_f_vals.items():
        if mode in offset_dict:
            delta_f = (num_days * val)
            query = saq.AE(delta_f)
            cost += query.generate_diff_priv_cost(alpha_dict[mode], offset_dict[mode])

    # Try and deduce from the privacy budget
    available_budget = safmt.deduct_budget(edb.pm_address, cost)
    if not available_budget:
        # Query could not complete, no budget remaining
        return {"success": False}

    is_return_aggregate = False
    metric_fn = metrics.summarize_by_local_date
    metric_list = [metric]
    ret_val = metric_fn(user_uuid,
              start_time, end_time,
              freq_name, metric_list, True)
    metrics_resp = ret_val['aggregate_metrics'][0]
    ret_dict = dict()
    # Metrics were successfully obtained
    if metrics_resp:
        metrics_data = metrics_resp[0]
        for key in offset_dict.keys():
            if key in metrics_data:
                ret_dict[key] = metrics_data[key]
            else:
                ret_dict[key] = 0
    else:
        for key in offset_dict.keys():
            ret_dict[key] = 0

    result = {"success" : True, "results": ret_dict}
    numpy_to_py(result)
    return result

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
