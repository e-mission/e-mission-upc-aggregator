#!/usr/bin/env bash
#Configure web server

# change python environment
source activate emission

# launch the webapp
./e-mission-py.bash emission/net/api/cfc_webapp.py
