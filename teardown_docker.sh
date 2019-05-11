#!/bin/bash

docker container stop $(docker ps -a -q)
yes | docker container prune
yes | docker volume prune
yes | docker network prune
