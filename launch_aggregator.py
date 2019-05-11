import subprocess, sys, requests
import json
import argparse
from emission.net.int_service.machine_configs import controller_ip, controller_port, register_user_endpoint


controller_addr = "{}:{}".format (controller_ip, controller_port)
username = "test_analyst"

# Default location of the query.
query_file = "query.json"

def main (csv_file, upperbound):
    r = requests.post (controller_addr + register_user_endpoint, json={'user':username})
    with open (query_file, "r") as f:
        query = json.load (f)
    if r.ok:
        ret = subprocess.Popen (["./e-mission-py.bash", "emission/net/ext_service/aggregator.py", controller_addr, "1", upperbound, username, "test-querier", csv_file])
        ret.wait ()
    else:
        print ("Error when registering the user.", file=sys.stderr)
        sys.exit (1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate the query request")
    parser.add_argument ("timestamp", type=int,
            help="Unique name to CSV file based on time")
    parser.add_argument ("upper_bound", type=int,
            help="Maximum number of users to request")
    items = parser.parse_args ()
    csv_file = "time_" + str (items.timestamp) + ".csv"
    main (csv_file, str (items.upper_bound))
