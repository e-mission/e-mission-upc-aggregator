# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

import requests
from emission.net.int_service.machine_configs import swarm_port, machines_list
from multiprocessing import Lock

# Current port the server should be listening on


class Machine ():
    total = 0
    def __init__ (self, baseaddr, serverPort, weight):
        self.baseaddr = baseaddr
        self.serverPort = serverPort
        self.weight = weight
        self.containers = []

    def addCloud (self, uuid):
        if self.weight == 0.0:
            return
        if Machine.total == 0 or len (self.containers) / Machine.total <= self.weight:
            resp = requests.post ("{}:{}/launch_cloud".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            self.containers.append (uuid)
            Machine.total += 1
            return "{}:{}".format (self.baseaddr, resp.text)
        return ""

    def addQuery (self, name, query_type, lock):
        if self.weight == 0.0:
            return
        if Machine.total == 0 or len (self.containers) / Machine.total <= self.weight:
            json_dict = {"name": name, "query": query_type, "lock": lock}
            resp = requests.post ("{}:{}/launch_querier".format (self.baseaddr, self.serverPort), json=json_dict)
            self.containers.append (name)
            Machine.total += 1
            return "{}:{}".format (self.baseaddr, resp.text)
        return ""
        

    def pauseContainer (self, uuid):
        if uuid in self.containers:
            resp = requests.post ("{}:{}/pause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def unpauseContainer (self, uuid):
        if uuid in self.containers:
            resp = requests.post ("{}:{}/unpause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def killContainer (self, uuid):
        if uuid in self.containers:
            resp = requests.post ("{}:{}/kill".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            print (resp)
            self.containers.remove (uuid)
            Machine.total -= 1
            return True 
        return False

    def clearContainers (self):
        Machine.total -= len (self.containers)
        resp = requests.post ("{}:{}/clear_all".format (self.baseaddr, self.serverPort))
        self.containers = []

        

# Takes in a list of machine tuples, where the first element is the IP_ADDR
# and the second element is the amount of memory available. This creates
# machine objects for each machine with the appropriate weight.
def setupMachines (machines):
    output = []
    total = 0.0
    for _, mem in machines:
        total += mem
    for ip, mem in machines:
        output.append (Machine (ip, swarm_port, mem / total))
    return output

# List consisting of the IP addresses any machines in the cluster.
# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = setupMachines (machines_list) 


# This file should be imported by the controller when not using kubernetes

# Helper function to allocate the Cloud instance
def createCloudInstance (uuid):
    for m in machines:
        res = m.addCloud (uuid)
        if res:
            return res
    return ""

# Helper function to pause the Cloud instance
def pauseCloudInstance (uuid):
    for m in machines:
        if m.pauseContainer (uuid):
            return


# Helper function to unpause the Cloud instance
def unpauseCloudInstance (uuid):
    for m in machines:
        if m.unpauseContainer (uuid):
            return

def createQueryInstance (name, query_type, lock):
    for m in machines:
        res = m.addQuery (name, query_type, lock)
        if res:
            return res
    return ""

def killQueryInstance (uuid):
    for m in machines:
        if m.killContainer (uuid):
            return

def clearContainers ():
    for m in machines:
        m.clearContainers ()
