import sys
from bottle import abort, route, run, post, get, request

key = None
profile = None

@route ("/")
def test():
    return "This is a test. Please ignore"

@post ("/key")
def process_key():
    global key
    if key:
        abort (403, "Key already given\n")
    else:
        key = request.json
        print (key)

@post ("/profile")
def process_profile():
    global profile
    if profile:
        abort (403, "Profile already given\n")
    else:
        profile = request.json
        print (profile)
    
@get ("/status")
def check_status ():
    ret_string = ""
    if key is None:
        ret_string += "Key needs to be sent\n"
    if profile is None:
        ret_string += "Profile needs to be sent\n"
    if not ret_string:
        ret_string = "All information received\n"
    return ret_string

@post ("/run")
def run_algorithm ():
    contents = request.json
    print (contents['algorithm'])
    if key is None:
        abort (403, "Cannot load data for algorithms with no key\n") 
    if profile is None:
        abort (403, "Cannot run algorithms with a missing profile\n")
    if contents["algorithm"] in profile:
        return "Algorithm is known and allowed. Running the algorithm...\n" 
    else:
        abort (403, "Algorithm not approved in profile.\n")
        
        
@post ("/store")
def store_data ():
    pass

@post ("/aggregate")
def run_aggregate ():
    pass

if __name__ == "__main__":
    if (len (sys.argv) == 1):
        run(host='localhost', port=4443, debug=True)
    elif (len (sys.argv) == 2):
        run(host='localhost', port= int (sys.argv[1]), debug=True)
    else:
        sys.stderr.write ("Error too many arguments to launch user cloud.\n")
