import datetime
import Compute_Layer.shared_resources.stream_data as clsrsd
from emission.net.int_service.machine_configs import certificate_bundle_path, load_endpoint, upc_port
import json
from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
from emission.core.get_database import url
from dateutil.parser import parse
# To support dynamic loading of client-specific libraries
import socket
import logging
import logging.config

import requests

try:
    config_file = open('conf/net/api/webserver.conf')
except:
    logging.debug("webserver not configured, falling back to sample, default configuration")
    config_file = open('conf/net/api/webserver.conf.sample')

config_data = json.load(config_file)
static_path = config_data["paths"]["static_path"]
python_path = config_data["paths"]["python_path"]
server_host = config_data["server"]["host"]
server_port = config_data["server"]["port"]
socket_timeout = config_data["server"]["timeout"]
log_base_dir = config_data["paths"]["log_base_dir"]
auth_method = config_data["server"]["auth"]

BaseRequest.MEMFILE_MAX = 1024 * 1024 * 1024 # Allow the request size to be 1G
# to accomodate large section sizes

print("Finished configuring logging for %s" % logging.getLogger())
app = app()

def get_last_event_from_server(upload_address, date):
    day_start = date.isoformat()
    day_end = (date + datetime.timedelta(days=1)).replace(hour=0, minute=0, 
            second=0, microsecond=0).isoformat()
    search_fields = [{"data.end_time": {"$lt": day_end, "$gt": day_start}}, {"_id": "False"}]
    should_sort = True
    sort = {'data.end_time': "False"}
    data, error = clsrsd.load_calendar_data(upload_address, search_fields, should_sort, sort)
    if error:
        return None
    else:
        data_values = data['data']
        if not data_values:
            return None
        else:
            return data_values[0]

@post("/get_last_event")
def get_arrival_time():
    upload_address = request.json['pm_address']
    # Extract the date and round down
    date = parse(request.json['date'])
    last_event = get_last_event_from_server(upload_address, date)
    if last_event is None:
        return None
    else:
        end_time = last_event['data']['end_time']
        location = last_event['data']['geo']
        return {'time' : end_time, 'geo': location}

if __name__ == '__main__':
    try:
        webserver_log_config = json.load(open("conf/log/webserver.conf", "r"))
    except:
        webserver_log_config = json.load(open("conf/log/webserver.conf.sample", "r"))

    logging.config.dictConfig(webserver_log_config)
    logging.debug("This should go to the log file")
    
    # To avoid config file for tests
    server_host = socket.gethostbyname(socket.gethostname())


    # The selection of SSL versus non-SSL should really be done through a config
    # option and not through editing source code, so let's make this keyed off the
    # port number
    if upc_port == 8000:
      # We support SSL and want to use it
      try:
        key_file = open('conf/net/keys.json')
      except:
        logging.debug("certificates not configured, falling back to sample, default certificates")
        key_file = open('conf/net/keys.json.sample')
      key_data = json.load(key_file)
      host_cert = key_data["host_certificate"]
      chain_cert = key_data["chain_certificate"]
      private_key = key_data["private_key"]

      run(host=server_host, port=upc_port, server='cheroot', debug=True,
          certfile=host_cert, chainfile=chain_cert, keyfile=private_key)
    else:
      # Non SSL option for testing on localhost
      print("Running with HTTPS turned OFF - use a reverse proxy on production")
      run(host=server_host, port=upc_port, server='cheroot', debug=True)

    # run(host="0.0.0.0", port=server_port, server='cherrypy', debug=True)
