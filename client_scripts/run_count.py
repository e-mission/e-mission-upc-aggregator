import argparse
import json
import socket
import requests
from shared_apis.service_router_api import request_service, delete_service
from conf.machine_configs import machines_use_tls, certificate_bundle_path

def run_count(uuid, pm_address, query_file):
    # Launch the count service
    query_address = request_service("Count")

    # Create the json for uploading to the count service
    json_entries = dict()
    json_entries['pm_address'] = pm_address
    json_entries['uuid'] = uuid
    with open(query_file, "r") as f:
        json_entries['query'] = json.load(f)
    address = "{}/count_query".format(query_address)
    error = False
    try:
        if machines_use_tls:
            r = requests.post(address, verify=certificate_bundle_path, json=json_entries, timeout=600)
        else:
            r = requests.post(address, json=json_entries, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    else:
        # Print the results
        print(json.dumps(r.json()))

    # Delete the count service
    delete_service(query_address)

    if error:
        assert(not error)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            Runs the pipeline service through the shared_api. There must be an existing
            PM running and the uuid used must be known.
            ''')
    parser.add_argument("uuid", type=str,
        help='''
            the uuid used to tag all of the user's records. This should eventually be removed
        ''')
    parser.add_argument("pm_address", type=str,
        help='''
            address of an existing pm. This pm is the target upload location
        ''')
    parser.add_argument("query_file", type=str,
        help='''
            the file that describes the query.
        ''')
    args = parser.parse_args()
    run_count(args.uuid, args.pm_address, args.query_file)
