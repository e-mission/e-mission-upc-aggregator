import requests
import json
import sys
import Compute_Layer.Services.emission_metrics.metrics as clsemm
from emission.net.int_service.machine_configs import certificate_bundle_path

def query_metrics(pm_address):
    timetype = "local_date"
    json_dict = dict()
    json_dict['pm_address'] = pm_address
    start_time = {
                    "year": 2015,
                    "month": 7,
                    "day": 22,
                    "timezone": "America/Los_Angeles"
                  }
    end_time = {
                    "year": 2015,
                    "month": 7,
                    "day": 23,
                    "timezone": "America/Los_Angeles"
                  }
    json_dict['start_time'] = start_time
    json_dict['end_time'] = end_time
    freq_name = "DAILY"
    json_dict['freq'] = freq_name
    metric_list = ["count", "distance", "duration"]
    json_dict['metric_list'] = metric_list
    offset_list = [24 * 28 * 12, 24 * 28 * 160000, 24 * 28 * 3600]
    json_dict['offset_list'] = offset_list
    alpha_list = [.05, .10, .15]
    json_dict['alpha_list'] = alpha_list
    r = requests.post("https://127.0.1.1:8000/metrics/local_date", json=json_dict, verify=certificate_bundle_path)
    results = r.json()
    print(results)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        query_metrics(sys.argv[1])
    else:
        print("This takes one argument, the user email!")
