import argparse
import json
from shared_apis.service_router_api import request_service, delete_service
from conf.machine_configs import machines_use_tls, certificate_bundle_path

def run_metrics(uuid, pm_address, metrics_file):
    # Launch the metrics service
    metrics_address = request_service("Metrics")

    # Create the json for uploading to the metrics service
    json_entries = dict()
    json_entries['pm_address'] = pm_address
    json_entries['uuid'] = uuid
    with open(metrics_file, "r") as f:
        metrics_contents = json.load(f)
    json_entries['start_time'] = metrics_contents['start_time']
    json_entries['end_time'] = metrics_contents['end_time']
    json_entries['freq'] = metrics_contents['freq']
    json_entries['metric'] = metrics_contents['metric']
    json_entries['offset'] = metrics_contents['offset']
    json_entries['alpha'] = metrics_contents['alpha']
    address = "{}/metrics/local_date".format(metrics_address)
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
        print(r.json())
    

    # Delete the metrics service
    delete_service(metrics_address)

    if error:
        assert(not error)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            Runs the pipeline service through the shared_api. There must be an existing
            PM running and the uuid used must be known.
            ''')
    parse.add_argument("uuid", type=str,
        help='''
            the uuid used to tag all of the user's records. This should eventually be removed
        ''')
    parse.add_argument("pm_address", type=str,
        help='''
            address of an existing pm. This pm is the target upload location
        ''')
    parse.add_argument("metrics_file", type=str,
        help='''
            the file that describes the metrics.
        ''')
    args = parser.parse_args()
    run_metrics(args.uuid, args.pm_address, args.metrics_file)
