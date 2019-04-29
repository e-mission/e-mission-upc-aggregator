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
        self.serverport = serverPort
        self.weight = weight
        self.containers = []

    def addCloud (uuid):
        if Machine.total == 0 or len (containers) / Machine.total <= self.weight:
            resp = requests.post ("{}:{}/launch_cloud".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            self.containers.append (uuid)
            Machine.total += 1
            return "{}:{}".format (self.baseaddr, resp.text)
        return ""

    def addQuery (name, query_type):
        if Machine.total == 0 or len (containers) / Machine.total <= self.weight:
            json_dict = {"name": uuid, "instance": instance, "query", query_type}
            resp = requests.post ("{}:{}/launch_querier".format (self.baseaddr, self.serverPort), json=json_dict)
            self.containers.append (uuid)
            Machine.total += 1
            return "{}:{}".format (self.baseaddr, resp.text)
        return ""
        

    def pauseContainer (uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/pause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def unpauseContainer (uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/unpause".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False

    def killContainer (uuid):
        if uuid in self.container:
            resp = requests.post ("{}:{}/kill".format (self.baseaddr, self.serverPort), json={'uuid':uuid})
            return True 
        return False
        


# List consisting of the IP addresses any machines in the cluster.
# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = []

machines.append (Machine ("10.142.33.235", serverPort, 1.0) #Nick's home machine in Weaver's office
machines.append (Machine ("128.32.37.205", serverPort, 0.0) #ante

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
        res = m.addQuery (uuid, i, query_type)
        if res:
            return res
    return ""

def killQueryInstance (uuid):
   for m in machines:
        if m.killContainer (uuid):
            return
