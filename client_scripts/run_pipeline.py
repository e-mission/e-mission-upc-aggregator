import argparse
import json
import requests
import socket
from shared_apis.service_router_api import request_service, delete_service
from conf.machine_configs import machines_use_tls, certificate_bundle_path

def run_pipeline(uuid, pm_address):
    # Launch the pipeline service
    pipeline_address = request_service("Pipeline")

    # Create the json for uploading to the pipeline service
    json_entries = dict()
    json_entries['pm_address'] = pm_address
    json_entries['uuid'] = uuid
    address = "{}/run_pipeline".format(pipeline_address)
    error = False
    try:
        if machines_use_tls:
            r = requests.post(address, verify=certificate_bundle_path, json=json_entries, timeout=600)
        else:
            r = requests.post(address, json=json_entries, timeout=600)
            print(r)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True

    # Delete the pipeline service
    delete_service(pipeline_address)

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
    args = parser.parse_args()
    run_pipeline(args.uuid, args.pm_address)
