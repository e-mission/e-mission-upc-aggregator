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

if __name__ == '__main__':
    np.random.seed(61297777)

    parser = argparse.ArgumentParser(prog="intake_single_user")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--user_email")
    group.add_argument("-u", "--user_uuid")

    args = parser.parse_args()

    clseprp.run_pipeline(args.user_email)
