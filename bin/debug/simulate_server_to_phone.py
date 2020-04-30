from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
# Exports all data for the particular user for the particular day
# Used for debugging issues with trip and section generation 
from future import standard_library
standard_library.install_aliases()
from builtins import *
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
import uuid
import datetime as pydt
import json
import bson.json_util as bju

import emission.net.api.usercache as enau
from emission.core.get_database import pm_address, run_upc

def save_server_to_phone(user_id_str, file_name):
    global pm_address, run_upc
    pm_address = user_id_str
    run_upc = True

    # TODO: Convert to call to get_timeseries once we get that working
    # Or should we even do that?
    retVal = enau.sync_server_to_phone(None)
    json.dump(retVal, open(file_name, "w"), default=bju.default, allow_nan=False, indent=4)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: %s <user> <file>" % (sys.argv[0]))
    else:
        save_server_to_phone(user_id_str=sys.argv[1], file_name=sys.argv[2])
