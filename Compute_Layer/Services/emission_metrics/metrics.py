from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response

import json
import logging
import logging.config
import socket
import numpy as np
import emission.net.api.metrics as metrics
import emission.core.get_database as edb
import Compute_Layer.shared_resources.queries as clsrq
import Compute_Layer.shared_resources.fake_mongo_types as clsrfmt
import datetime
import pytz
from emission.net.int_service.machine_configs import upc_port

# Dictionary that holds the static delta f multipler values for each result type
# We assume the options are count (in trips), distance (in meters), and
# duration (in seconds). To compute the delta_f we consider the maximum
# and minimum value between the most extreme mode of transportation, driving in our
# case. Our delta_f is also dependent on the range of time over which we query, so
# we provide metrics as a maximum that can be traveled per hour (which is the finest
# granularity at which we let someone query data. Planning conservatively,
# we assume that the maximum duration is a full hour. The maximum distance
# traveled by in 1 hour by car. Rather than consider the most ever travel by car
# in one hour, we will neglect racecar drivers and suggest that no one will drive
# faster than an average of 160 km/hour. Finally for counts there is no clear defining
# trip count. If you assume each trip takes at least 5 minutes then no more than 12 trips
# could happen per hour. This is likely far more conservative than is needed and these 
# values should not be considered with any rigor.
delta_f_dict = {
        "count": 12, # Units of trips per hour
        "distance": 160000, #Units of meters per hour
        "duration": 3600 # Units of seconds per hour
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



# We assume that date times only consist of at most year, month, day, hour, and tz.
# if month and day are not provided we will assume they represent 1 each, if only
# day is not provided we will assume it represents 1.
def extractDatetimeFromDict(datetime_dict):
    year = datetime_dict['year']
    if "month" in datetime_dict:
        month = datetime_dict['month']
        if 'day' in datetime_dict:
            day = datetime_dict['day']
            if 'hour' in datetime_dict:
                hour = datetime_dict['hour']
            else:
                hour = 0
        else:
            day = 1
    else:
        month = 1
        day = 1
        hour = 0
    timezone = pytz.timezone(datetime_dict['timezone'])
    return datetime.datetime(year, month, day, hour, tzinfo = timezone)


@post('/metrics/local_date')
def summarize_metrics():
    print("reached")
    edb.pm_address = request.json['pm_address']
    user_uuid = 23 # Dummy id used as a placeholder
    start_time = request.json['start_time']
    end_time = request.json['end_time']
    freq_name = request.json['freq']
    metric_list = request.json['metric_list']
    offset_list = request.json['offset_list']
    alpha_list = request.json['alpha_list']

    # Calculate the range of time in hours
    end_datetime = extractDatetimeFromDict(end_time)
    start_datetime = extractDatetimeFromDict(start_time)
    num_hours = ((end_datetime - start_datetime).total_seconds() / 3600.0)

    # Look up delta f by metrics list
    # Assume we must run the whole query at once, so we deduct from the privacy budget once
    cost = 0
    for i, name in enumerate(metric_list):
        assert (name in delta_f_dict)
        delta_f = (num_hours * delta_f_dict[name])
        query = clsrq.AE(delta_f)
        cost += query.generate_diff_priv_cost(alpha_list[i], offset_list[i])
    print(cost)

    # Try and deduce from the privacy budget
    available_budget = clsrfmt.deduct_budget(edb.pm_address, cost)
    if not available_budget:
        # Query could not complete, no budget remaining
        return {"success": ""}

    is_return_aggregate = False
    metric_fn = metrics.summarize_by_local_date
    ret_val = metric_fn(user_uuid,
              start_time, end_time,
              freq_name, metric_list, is_return_aggregate)
    # logging.debug("ret_val = %s" % bson.json_util.dumps(ret_val))
    print(ret_val)
    result = {"success" : True, "results": ret_val}
    numpy_to_py(result)
    return result

if __name__ == '__main__':
    try:
        webserver_log_config = json.load(open("conf/log/webserver.conf", "r"))
    except:
        webserver_log_config = json.load(open("conf/log/webserver.conf.sample", "r"))

    logging.config.dictConfig(webserver_log_config)
    logging.debug("This should go to the log file")
    
    # To avoid config file for tests
    server_host = socket.gethostbyname(socket.gethostname())


    # The selection of SSL versus non-SSL should really be done through a config
    # option and not through editing source code, so let's make this keyed off the
    # port number
    if upc_port == 8000:
      # We support SSL and want to use it
      try:
        key_file = open('conf/net/keys.json')
      except:
        logging.debug("certificates not configured, falling back to sample, default certificates")
        key_file = open('conf/net/keys.json.sample')
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

    # run(host="0.0.0.0", port=server_port, server='cherrypy', debug=True)
