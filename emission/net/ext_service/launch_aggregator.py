import subprocess, sys, requests
import json
import argparse
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint, certificate_bundle_path


controller_addr = "{}:{}".format (controller_ip, controller_port)
username = "test_analyst"

# Default location of the query.
# query_file = "query.json"

def main (query_file, csv_file, upperbound):
    r = requests.post (controller_addr + register_user_endpoint, json={'user':username}, verify=certificate_bundle_path)
    if r.ok:
        ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/aggregator.py", query_file, controller_addr, "1", upperbound, username, "test-querier", csv_file])
        ret.wait ()
    else:
        print ("Error when registering the user.", file=sys.stderr)
        sys.exit (1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate the query request")
    parser.add_argument ("query_file", type=str,
            help="Query to conduct")
    parser.add_argument ("csv_name", type=str,
            help="Unique name to CSV file based on time")
    parser.add_argument ("upper_bound", type=int,
            help="Maximum number of users to request")
    items = parser.parse_args ()
    main (items.query_file, items.csv_name, str (items.upper_bound))
