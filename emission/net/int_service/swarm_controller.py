# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

import requests

# Current port the server should be listening on
serverPort = 54321


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

    def addQuery (self, name, query_type):
        if self.weight == 0.0:
            return
        if Machine.total == 0 or len (self.containers) / Machine.total <= self.weight:
            json_dict = {"name": name, "query": query_type}
            resp = requests.post ("{}:{}/launch_querier".format (self.baseaddr, self.serverPort), json=json_dict)
            self.containers.append (name)
            Machine.total += 1
            return "{}:{}".format (self.baseaddr, resp.text)
        return ""
        

    def pauseContainer (self, uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/pause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def unpauseContainer (self, uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/unpause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def killContainer (self, uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/kill".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            self.container.remove (uuid)
            Machine.total -= 1
            return True 
        return False
        


# List consisting of the IP addresses any machines in the cluster.
# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = []

machines.append (Machine ("http://128.32.37.205", serverPort, .75)) #ante
machines.append (Machine ("http://34.218.199.35", serverPort, .25)) #Jack's AWS

# Right now we give ante no weight cause nothing is configured. We will launch
# the server with sudo to enable ante

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

def createQueryInstance (name, query_type):
    for m in machines:
        res = m.addQuery (name, query_type)
        if res:
            return res
    return ""

def killQueryInstance (uuid):
    for m in machines:
        if m.killContainer (uuid):
            return
