import subprocess, sys, requests

controller_addr = "http://localhost:4040"
username = "test_analyst"

def main ():
    r = requests.post (controller_addr + "/profile/create", json={'user':username})
    if r.ok:
        subprocess.run (["python", "emission/net/ext_service/aggregator.py", "query_goes_here", controller_addr, "4", username, "test-querier"])
    else:
        print ("Error when registering the user.", f=sys.stderr)
        sys.exit (1)

if __name__ == "__main__":
    main ()
