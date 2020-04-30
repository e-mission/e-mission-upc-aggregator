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

import emission.pipeline.intake_stage as epi
import emission.core.wrapper.user as ecwu
import Compute_Layer.Services.emission_pipeline.run_pipeline as clseprp

from emission.net.int_service.machine_configs import certificate_bundle_path 

if __name__ == '__main__':
    np.random.seed(61297777)

    parser = argparse.ArgumentParser(prog="intake_single_user")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--user_email")
    group.add_argument("-u", "--user_uuid")

    args = parser.parse_args()
    json_entries = dict()
    json_entries['pm_address'] = args.user_email

    r = requests.post("https://127.0.1.1:8000/run_pipeline", json=json_entries, 
            timeout=6000, verify=certificate_bundle_path)
