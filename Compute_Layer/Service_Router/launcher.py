# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

import requests
import numpy as np
from emission.net.int_service.machine_configs import swarm_port, machines_list, certificate_bundle_path

randlist = []

class Machine ():
    total = 0
    def __init__ (self, baseaddr, serverPort, weight):
        self.baseaddr = baseaddr
        self.serverPort = serverPort
        self.weight = weight
        self.containers = []

    def spawnService (self, uuid, use_kubernetes, service_name, service_file, pod_file=None):
        if self.weight == 0.0:
            return
        json_dict = {'uuid':uuid, 'use_kubernetes': use_kubernetes, 'service_name': service_name,
                'service_file' : service_file, 'pod_file': pod_file}
        resp = requests.post ("{}:{}/spawn_service".format (self.baseaddr, self.serverPort), 
                json=json_dict, verify=certificate_bundle_path)
        print(resp.text)
        components = resp.text.split()
        container_name = components[0]
        container_port = components[1]
        self.containers.append (container_name)
        Machine.total += 1
        return (container_name, "{}:{}".format (self.baseaddr, container_port))

    def killContainer (self, name):
        if name in self.containers:
            resp = requests.post ("{}:{}/kill".format (self.baseaddr, self.serverPort), json={'uuid':name}, verify=certificate_bundle_path)
            print (resp)
            self.containers.remove (name)
            Machine.total -= 1
            return True 
        return False

    def clearContainers (self):
        Machine.total -= len (self.containers)
        resp = requests.post ("{}:{}/clear_all".format (self.baseaddr, self.serverPort), verify=certificate_bundle_path)
        self.containers = []

    def setupNetwork (self):
        resp = requests.post ("{}:{}/create_network".format (self.baseaddr, self.serverPort), verify=certificate_bundle_path)
        

# Takes in a list of machine tuples, where the first element is the IP_ADDR
# and the second element is the amount of memory available. This creates
# machine objects for each machine with the appropriate weight.
def setupMachines (machines):
    output = []
    total = 0.0
    for _, mem in machines:
        total += mem
    total_rand = 0.0
    for ip, mem in machines:
        output.append (Machine (ip, swarm_port, mem / total))
        total_rand += mem / total
        randlist.append (total_rand)
    return output

# List consisting of the IP addresses any machines in the cluster.
# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = setupMachines (machines_list) 


# This file should be imported by the controller when not using kubernetes

# Helper function to allocate the Cloud instance
def spawnServiceInstance (uuid, use_kubernetes, service_name, service_file, pod_file=None):
    val = np.random.random ()
    i = 0
    while val > randlist[i]:
        i += 1
    return machines[i].spawnService (uuid, use_kubernetes, service_name, service_file, pod_file)


def killInstance (name):
    for m in machines:
        if m.killContainer (name):
            return

def clearContainers ():
    for m in machines:
        m.clearContainers ()

def setupNetworks ():
    for m in machines:
        m.setupNetwork ()
