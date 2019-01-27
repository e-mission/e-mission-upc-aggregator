#!/usr/bin/python3
import sys
import os
import requests
from bottle import route, run, get, post, request
import json
import uuid
import subprocess
import atexit
import docker
import socket
import time
import signal
from docker.types import Mount
import threading
import http.client

port = 2000
json_data = json.load(open("mock_data.json"))
list_of_containers = list(json.load(open("mock_data.json")).keys())
client = docker.from_env()
controller_ip = socket.gethostbyname(socket.gethostname()) + ":" + str(port)
path = os.path.expanduser("~/e-mission-server/")
uuid_counter = 0
uuid_set = set()
uuid_counter_lock = threading.Lock()
ready_to_proceed = threading.Event()
# container_port = 1025

class DockerThread(threading.Thread):
        def __init__(self, container, query_type, user_uuid, agg_ip, privacy_budget, controller_uuid):
                threading.Thread.__init__(self)
                self.container = container
                self.query_type = query_type
                self.user_uuid = user_uuid
                self.agg_ip = agg_ip
                self.privacy_budget = privacy_budget
                self.controller_uuid = controller_uuid
        def run(self):
                self.container.unpause()
                output = self.container.exec_run('bash user_enclave.bash ' + self.query_type + ' ' + self.user_uuid + ' ' + self.agg_ip + ' ' + controller_ip + ' ' + self.controller_uuid + ' ' + self.privacy_budget)
                print(output)
                self.container.pause()

@get("/")
def home():
        return "hello!"

@post('/upload_info')
def upload():
        pass

@get('/remove_containers')
def remove_containers():
    for container in list_of_containers:
        container[0].remove(force=True)
    return "User containers removed"
@post('/user_finished')
def user_finished():
    """
    Aggregator sends post request here to let controller know
    that the container with given UUID's message has been received
    """
    global uuid_counter
    request_dict = json.loads(request.body.read().decode('UTF-8'))
    controller_uuid = uuid.UUID(request_dict['controller_uuid'])
    if controller_uuid in uuid_set:
        with uuid_counter_lock:
            uuid_counter += 1
            print(uuid_counter)
        if uuid_counter == len(uuid_set):
            ready_to_proceed.set()
        return "Done with current user_finished call"
    return "stop trying to spam me, malicious entity!"

@post('/request_query')
def query_start():
        """
        1. Read list of enclaves from file
        2. Wake them up with docker resume
        3. Ask for query from them
        """
        request_dict = json.loads(request.body.read().decode('UTF-8'))
        query_type = str(request_dict['query_type'])
        privacy_budget = str(request_dict['privacy_budget'])
        print(request_dict)
        threads = []
        aggregator_ip = request.environ['REMOTE_ADDR'] + ':2001'
        print("aggregator_ip: " + str(aggregator_ip))
        print("Length of list of containers: " + str(len(list_of_containers)))
        batch_size = 10
        global uuid_counter, uuid_set, ready_to_proceed
        ready_to_proceed = threading.Event()
        uuid_counter, uuid_set = 0, set()
        for j in range(0, int(len(list_of_containers) / batch_size) + 1):
                for i in range(min(int(len(list_of_containers) - j * batch_size), batch_size)):
                        rand_uuid = str(uuid.uuid1())
                        uuid_set.add(uuid.UUID(rand_uuid))
                        send_to_agg = http.client.HTTPConnection(aggregator_ip)
                        send_to_agg_data = json.dumps({'controller_ip':controller_ip, 'controller_uuid':rand_uuid})
                        send_to_agg.request("POST", "/add_uuid_map", send_to_agg_data)
                        response = send_to_agg.getresponse()
                        container = list_of_containers[j * batch_size + i]
                        thread = DockerThread(container[0], query_type, container[1], aggregator_ip, privacy_budget, rand_uuid)
                        thread.start()
                        threads.append(thread)
                for thread in threads:
                    thread.join()
        ready_to_proceed.wait() #wait until all requests received by agg
        return "Finished"       

@get('/start_containers')
def start():
        mount = Mount(target='/usr/src/app/conf/storage/db.conf', source= path + 'conf/storage/db.conf', type='bind')
        for i in range(len(list_of_containers)):
                container = list_of_containers[i]
                print(container)
                #json_data[container]["privacy_budget"] = 10
                list_of_containers[i] = [client.containers.run('skxu3/emission-scone3.5', command = "tail -f /dev/null",
                        name = container, remove=True, devices=['/dev/isgx'], network='e-mission', mounts=[mount], volumes={path :{'bind':'/usr/src/myapp','mode':'rw'}}, working_dir='/usr/src/myapp', detach=True),
                        container]
                list_of_containers[i][0].pause()
        print(list_of_containers)
        #with open("mock_data.json", "w") as jsonFile:
        #    json.dump(json_data, jsonFile)
        return "User containers started"

if __name__ == "__main__":
    atexit.register(remove_containers)
    start()
    run(port=port, host='0.0.0.0',debug=True, server='paste')
    #threading.Thread(target=run, args=(2000, '0.0.0.0')).start()
