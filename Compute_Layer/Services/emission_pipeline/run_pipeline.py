from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import *
import json
import logging
import numpy as np
import arrow
from uuid import UUID
import time

from emission.net.api.bottle import route, post, get, run, template, static_file, request, app, HTTPError, abort, BaseRequest, JSONPlugin, response
from emission.core.get_database import url
from dateutil.parser import parse
# To support dynamic loading of client-specific libraries
import socket
import logging.config

import emission.core.get_database as edb
import emission.core.timer as ect

import emission.core.wrapper.pipelinestate as ecwp

import emission.net.usercache.abstract_usercache_handler as euah
import emission.net.usercache.abstract_usercache as enua
import emission.storage.timeseries.abstract_timeseries as esta
import emission.storage.timeseries.aggregate_timeseries as estag

import emission.analysis.intake.cleaning.filter_accuracy as eaicf
import emission.analysis.intake.segmentation.trip_segmentation as eaist
import emission.analysis.intake.segmentation.section_segmentation as eaiss
import emission.analysis.intake.cleaning.location_smoothing as eaicl
import emission.analysis.intake.cleaning.clean_and_resample as eaicr
import emission.analysis.classification.inference.mode.pipeline as eacimp
import emission.net.ext_service.habitica.executor as autocheck

import emission.storage.decorations.stats_queries as esds


dummy_id = 23

"""
    Steps to change:
        1. Find all uuid spots and add clauses for if type
        2. Replace all stores with store data stream
        3. Replace all loads with load data stream
        4. Integrate db fetches with that process as well
        5. Filter uuid
"""
@post("/run_pipeline")
def run_pipeline():
    edb.pm_address = request.json['pm_address']
    # uuid is never needed
    uuid = dummy_id
    uh = euah.UserCacheHandler.getUserCacheHandler(uuid)

    with ect.Timer() as uct:
        logging.info("*" * 10 + "moving to long term" + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "moving to long term" + "*" * 10)
        uh.moveToLongTerm()

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.USERCACHE.name,
                             time.time(), uct.elapsed)


    # Hack until we delete these spurious entries
    # https://github.com/e-mission/e-mission-server/issues/407#issuecomment-2484868
    # Hack no longer works after the stats are in the timeseries because
    # every user, even really old ones, have the pipeline run for them,
    # which inserts pipeline_time stats.
    # Let's strip out users who only have pipeline_time entries in the timeseries
    # I wonder if this (distinct versus count) is the reason that the pipeline has
    # become so much slower recently. Let's try to actually delete the
    # spurious entries or at least mark them as obsolete and see if that helps.
    print(edb.get_timeseries_db().find({"user_id": uuid}).distinct("metadata.key"))

    if edb.get_timeseries_db().find({"user_id": uuid}).distinct("metadata.key") == ["stats/pipeline_time"]:
        logging.debug("Found no entries for %s, skipping" % uuid)
        return

    with ect.Timer() as aft:
        logging.info("*" * 10 + "UUID %s: filter accuracy if needed" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: filter accuracy if needed" % uuid + "*" * 10)
        eaicf.filter_accuracy(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.ACCURACY_FILTERING.name,
                             time.time(), aft.elapsed)

    with ect.Timer() as tst:
        logging.info("*" * 10 + "UUID %s: segmenting into trips" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: segmenting into trips" % uuid + "*" * 10)
        eaist.segment_current_trips(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.TRIP_SEGMENTATION.name,
                             time.time(), tst.elapsed)

    with ect.Timer() as sst:
        logging.info("*" * 10 + "UUID %s: segmenting into sections" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: segmenting into sections" % uuid + "*" * 10)
        eaiss.segment_current_sections(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.SECTION_SEGMENTATION.name,
                             time.time(), sst.elapsed)

    with ect.Timer() as jst:
        logging.info("*" * 10 + "UUID %s: smoothing sections" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: smoothing sections" % uuid + "*" * 10)
        eaicl.filter_current_sections(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.JUMP_SMOOTHING.name,
                             time.time(), jst.elapsed)

    with ect.Timer() as crt:
        logging.info("*" * 10 + "UUID %s: cleaning and resampling timeline" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: cleaning and resampling timeline" % uuid + "*" * 10)
        eaicr.clean_and_resample(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.CLEAN_RESAMPLING.name,
                             time.time(), crt.elapsed)

    with ect.Timer() as crt:
        logging.info("*" * 10 + "UUID %s: inferring transportation mode" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: inferring transportation mode" % uuid + "*" * 10)
        eacimp.predict_mode(uuid)

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.MODE_INFERENCE.name,
                             time.time(), crt.elapsed)

    with ect.Timer() as ogt:
        logging.info("*" * 10 + "UUID %s: storing views to cache" % uuid + "*" * 10)
        print(str(arrow.now()) + "*" * 10 + "UUID %s: storing views to cache" % uuid + "*" * 10)
        # use store data
        uh.storeViewsToCache()

    esds.store_pipeline_time(uuid, ecwp.PipelineStages.OUTPUT_GEN.name,
                             time.time(), ogt.elapsed)

if __name__ == '__main__':
    try:
        webserver_log_config = json.load(open("conf/log/webserver.conf", "r"))
    except:
        webserver_log_config = json.load(open("conf/log/webserver.conf.sample", "r"))

    logging.config.dictConfig(webserver_log_config)
    logging.debug("This should go to the log file")
    
    # To avoid config file for tests
    server_host = socket.gethostbyname(socket.gethostname())

    upc_port = 80

    # The selection of SSL versus non-SSL should really be done through a config
    # option and not through editing source code, so let's make this keyed off the
    # port number
    if upc_port == 443:
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
