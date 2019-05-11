import subprocess, sys, requests
import json

controller_addr = "http://128.32.37.205:4040"
username = "test_analyst"

# Default location of the query.
query_file = "query.json"

def main (csv_file):
    r = requests.post (controller_addr + "/profile/create", json={'user':username})
    with open (query_file, "r") as f:
        query = json.load (f)
        print(query)
    if r.ok:
        subprocess.run (["python", "emission/net/ext_service/aggregator.py", controller_addr, "4", username, "test-querier", csv_file])

        # Put timer here, gets the time of launching the aggregator.
    else:
        print ("Error when registering the user.", file=sys.stderr)
        sys.exit (1)

if __name__ == "__main__":
    timestamp = sys.argv[1]
    csv_file = "time_" + timestamp + ".csv"
    main (csv_file)
