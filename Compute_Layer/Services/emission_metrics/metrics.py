from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response

import json
import numpy as np
import emission.net.api.metrics as metrics
import emission.core.get_database as edb
import Compute_Layer.shared_resources.queries as clsrq
import Compute_Layer.shared_resources.fake_mongo_types as clsrfmt
import datetime
import pytz

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


#@post('/metrics/local_date')
def summarize_metrics(pm_address, start_time, end_time, freq_name, metric_list, offset_list, alpha_list):
    edb.pm_address = pm_address
    user_uuid = 23 # Dummy id used as a placeholder
    """
    start_time = request.json['start_time']
    end_time = request.json['end_time']
    freq_name = request.json['freq']
    """

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
    available_budget = clsrfmt.deduct_budget(pm_address, cost)
    if not available_budget:
        # Query could not complete, no budget remaining
        return None

    #metric_list = request.json['metric_list']
    is_return_aggregate = False
    metric_fn = metrics.summarize_by_local_date
    ret_val = metric_fn(user_uuid,
              start_time, end_time,
              freq_name, metric_list, is_return_aggregate)
    # logging.debug("ret_val = %s" % bson.json_util.dumps(ret_val))
    return ret_val
