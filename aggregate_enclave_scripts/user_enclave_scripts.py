import sys
import json
import ast
import os
#import requests
import http.client
data_path = "e-mission-upc-aggregator/aggregate_enclave_scripts/mock_data.json"
json_data = json.load(open(data_path))

def query(query_type, e_id, aggregator_ip, controller_ip, controller_uuid, privacy_budget):
    if query_type == "sum":
        try:
            h1 = http.client.HTTPConnection(aggregator_ip)
            user_data = json_data[e_id]["data"]["speeds"]
            if user_data == []:
                data = json.dumps({'response':'none'})
            else:
                remaining_budget = float(json_data[e_id]["privacy_budget"])
                privacy_budget = float(privacy_budget)
                if remaining_budget >= privacy_budget:
                    data = json.dumps({'response':'yes', 'value': sum(user_data), 'controller_ip': controller_ip, 'controller_uuid': controller_uuid})
                    #json_data[e_id]["privacy_budget"] = remaining_budget - privacy_budget
                    with open(data_path, "w") as jsonFile:
                        json.dump(json_data, jsonFile)
                else:
                    data = json.dumps({'response':'none', 'controller_ip': controller_ip, 'controller_uuid': controller_uuid})
                h1.request("POST", "/add_to_result_list", data)
        except:
            data = json.dumps({'response':'none', 'controller_ip': controller_ip, 'controller_uuid': controller_uuid})
            h1.request("POST", "/add_to_result_list", data)
    else:
        raise NotImplementedError

if __name__ == "__main__":
    print(sys.argv)
    query_type = sys.argv[1]
    enclave_id = sys.argv[2]
    aggregator_ip = sys.argv[3]
    controller_ip = sys.argv[4]
    controller_uuid = sys.argv[5]
    privacy_budget = sys.argv[6]
    query(query_type, enclave_id, aggregator_ip, controller_ip, controller_uuid, privacy_budget)
