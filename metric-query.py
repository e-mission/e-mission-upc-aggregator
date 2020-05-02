import requests
import json
import sys
import Compute_Layer.Services.emission_metrics.metrics as clsemm

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
    #r = requests.post("http://localhost:8080/result/metrics/{}".format(timetype), json=json_dict)
    #results = r.json()
    offset_list = [24 * 12, 24 * 160000, 24 * 3600]
    alpha_list = [.05, .10, .15]
    result = clsemm.summarize_metrics(pm_address, start_time, end_time, freq_name, metric_list,
            offset_list, alpha_list)
    print(result)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        query_metrics(sys.argv[1])
    else:
        print("This takes one argument, the user email!")
