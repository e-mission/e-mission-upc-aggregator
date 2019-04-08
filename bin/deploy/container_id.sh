#!/bin/bash
docker container ls | grep -o -P $1"[^\s]*"
