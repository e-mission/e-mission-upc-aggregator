import numpy as np
import sys, subprocess
from bottle import abort, route, run, post, get, request

userclouds = dict ()

@route ("/")
def test():
    return "This is a test. Please ignore"

@post ("/usercloud")
def spawn_usercloud ():
    contents = request.json
    if contents in userclouds:
        return userclouds[contents]
    else:
        not_spawn = True
        while (not_spawn):
            # select a random port and hope it works
            port = np.random.randint (low=2000, high = (pow (2, 16) - 1))
            res = subprocess.Popen (['python', 'usercloud.py', str (port)])
            # Check if it instantly crashes which suggests the port is no good
            try:
                res.wait (.5)
            except subprocess.TimeoutExpired:
                not_spawn = False
        output = "http://localhost:" + str (port)
        userclouds[contents] = output
        return output
    

if __name__ == "__main__":
    if (len (sys.argv) == 1):
        run(host='localhost', port=8080, debug=True)
    elif (len (sys.argv) == 2):
        run(host='localhost', port= int (sys.argv[1]), debug=True)
    else:
        sys.stderr.write ("Error too many arguments to launch known access location.\n")
