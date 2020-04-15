import json

services = {}
services["user-cloud"] = {"service-file":"docker/docker-compose.yml"}
services["basic-querier"] = {"service-file":"docker/docker-compose-test-querier.yml"}

with open("service.json", "w") as output:
    json.dump(services, output)
