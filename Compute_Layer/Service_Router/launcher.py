# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.

import requests
import numpy as np
from emission.net.int_service.machine_configs import swarm_port, machines_list
import Compute_Layer.Service_Router.swarm as clsrs

class Machine ():
    total = 0
    def __init__ (self, baseaddr):
        self.baseaddr = baseaddr

    def spawnService (self, service_file, pod_file):
        container_name, container_port = clsrs.spawn_service(service_file, pod_file)
        return (container_name, "{}:{}".format (self.baseaddr, container_port))

    def killContainer (self, name):
        clsrs.kill(name)

    def clearContainers (self):
        clsrs.clear_all()

    def setupNetwork (self):
        clsrs.create_network()
        

# Takes in a list of machine tuples, where the first element is the IP_ADDR
# and the second element is the amount of memory available. This creates
# machine objects for each machine with the appropriate weight.
def setupMachines (machines):
    output = []
    for ip in machines:
        output.append (Machine (ip))
    return output

# List consisting of the IP addresses any machines in the cluster.
# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = setupMachines (machines_list) 


# This file should be imported by the controller when not using kubernetes

# Helper function to allocate the Cloud instance
def spawnServiceInstance (service_file, pod_file):
    m = machines[0]
    return m.spawnService (service_file, pod_file)


def killInstance(name):
    m = machines[0]
    m.killContainer(name)

def clearContainers():
    m = machines[0]
    m.clearContainers()

def setupNetworks():
    m = machines[0]
    m.setupNetwork()
