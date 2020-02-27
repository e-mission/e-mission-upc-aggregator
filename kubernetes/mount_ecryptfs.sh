#!/bin/bash
mount -t ecryptfs /data/db /data/db -o no_sig_cache
keyctl clear @u
