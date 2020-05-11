from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import json
import logging
from logging import config
import argparse
import numpy as np
import uuid

import requests

import emission.pipeline.intake_stage as epi
import emission.core.wrapper.user as ecwu
import Compute_Layer.Services.emission_pipeline.run_pipeline as clseprp


if __name__ == '__main__':
    np.random.seed(61297777)

    parser = argparse.ArgumentParser(prog="intake_single_user")
    parser.add_argument("pm_addr", type=str)
    parser.add_argument("pipeline_addr", type=str)

    args = parser.parse_args()
    json_entries = dict()
    json_entries['pm_address'] = args.pm_addr

    print(args.pipeline_addr)
    r = requests.post("{}/run_pipeline".format(args.pipeline_addr), json=json_entries, 
            timeout=600000)
