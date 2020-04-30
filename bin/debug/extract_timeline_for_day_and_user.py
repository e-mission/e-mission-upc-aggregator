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

import emission.core.get_database as edb
from emission.core.get_database import pm_address, run_upc

def export_timeline(user_id_str, day_str, file_name):
    global pm_address, run_upc
    pm_address = user_id_str
    run_upc = True

    # day_dt = pydt.datetime.strptime(day_str, "%Y-%m-%d").date()
    day_dt = pydt.datetime.strptime(day_str, "%Y-%m-%d")
    logging.debug("day_dt is %s" % day_dt)
    # TODO: Convert to call to get_timeseries once we get that working
    # Or should we even do that?
    user_query = {'user_id': None}
    date_query = {'metadata.write_local_dt.year': day_dt.year,
	'metadata.write_local_dt.month': day_dt.month,
	'metadata.write_local_dt.day': day_dt.day}
    final_query = user_query
    final_query.update(date_query)
    entry_list = list(edb.get_timeseries_db().find(final_query))
    logging.info("Found %d entries" % len(entry_list))
    json.dump(entry_list, open(file_name, "w"), default=bju.default, allow_nan=False, indent=4)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: %s <user> <day> <file>" % (sys.argv[0]))
    else:
        export_timeline(user_id_str=sys.argv[1], day_str=sys.argv[2], file_name=sys.argv[3])
