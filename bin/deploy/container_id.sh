#!/bin/bash
docker container ls | perl -nle 'print $& while m{'$1'[^\s]*}g' 
