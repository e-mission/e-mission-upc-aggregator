# This file is meant to function as a temporary replacement for the
# distribution of machines while Kubernetes is not working. This is
# necessary because docker swarm does not support privilege escalation,
# so until we have access to Kubernetes we need a temporary alternative
# to use multiple machines in a cluster.
import json
import requests
import subprocess
import numpy as np
from conf.machine_configs import upc_port, swarm_port, machines_dict, upc_mode, machines_use_tls, certificate_bundle_path
from tempfile import NamedTemporaryFile

class Machine ():
    total = 0
    def __init__ (self, baseaddr, weight):
        self._baseaddr = baseaddr
        self._weight = weight

    def getSwarmaddr(self):
        return "{}:{}".format(self._baseaddr, swarm_port)

    def getWeight(self):
        return self._weight

    # For an implementation in kubernetes we assume that there are two files, a pod file and
    # a service file. If the implementation is running in docker we instead assume a single
    # file, which we will always label as the service file.
    def spawnService (self, service_file, pod_file, server_container_name):
        if upc_mode == "kubernetes":
            if pod_file is None or server_container_name is None:
                raise HTTPError(403, "Kubernetes specified but no pod file is present")
            with open(service_file, "r") as service:
                with open(pod_file, "r") as pod:
                    container_name, container_port = launch_unique_service(json.load(service), json.load(pod), server_container_name)
        elif upc_mode == "docker":
            json_dict = dict()
            json_dict['compose_file'] = service_file
            target_address = "{}/launch_service".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path, json=json_dict)
            else:
                r = requests.post(target_address, json=json_dict)
            if r.ok:
                json_results = r.json()
                container_name, container_port = json_results['name'], json_results['port']
            else:
                raise HTTPError(403, "Error ecountered while spawning service. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")
        return (container_name, "{}:{}".format (self._baseaddr, container_port))

    def pauseService (self):
        if upc_mode == "kubernetes":
            # There is no support for pausing in Kubernetes right now.
            # However, to allow the same scripts to run on both kubernetes and docker
            # we will not throw any exceptions
            pass
        elif upc_mode == "docker":
            json_dict = dict()
            json_dict['name'] = name
            target_address = "{}/pause".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path, json=json_dict)
            else:
                r = requests.post(target_address, json=json_dict)
            if r.ok:
                json_results = r.json()
                return json_results['success']
            else:
                raise HTTPError(403, "Error ecountered while pausing service. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")

    def resumeService (self):
        if upc_mode == "kubernetes":
            # There is no support for pausing in Kubernetes right now.
            # However, to allow the same scripts to run on both kubernetes and docker
            # we will not throw any exceptions
            pass
        elif upc_mode == "docker":
            json_dict = dict()
            json_dict['name'] = name
            target_address = "{}/unpause".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path, json=json_dict)
            else:
                r = requests.post(target_address, json=json_dict)
            if r.ok:
                json_results = r.json()
                return json_results['success']
            else:
                raise HTTPError(403, "Error ecountered while resuming service. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")

    def killContainer (self, name):
        if upc_mode == "kubernetes":
            subprocess.run(["kubectl", "delete", "service", name ,"--namespace=default"])
            subprocess.run(["kubectl", "delete", "pod", name ,"--namespace=default"])
            return True
        elif upc_mode == "docker":
            json_dict = dict()
            json_dict['name'] = name
            target_address = "{}/kill".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path, json=json_dict)
            else:
                r = requests.post(target_address, json=json_dict)
            if r.ok:
                json_results = r.json()
                return json_results['success']
            else:
                raise HTTPError(403, "Error ecountered while deleting service. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")

    def clearContainers (self):
        if upc_mode == "kubernetes":
            subprocess.run(["kubectl", "delete", "--all", "services" ,"--namespace=default"])
            subprocess.run(["kubectl", "delete", "--all", "pods" ,"--namespace=default"])
        elif upc_mode == "docker":
            json_dict = dict()
            json_dict['name'] = name
            target_address = "{}/clear_all".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path, json=json_dict)
            else:
                r = requests.post(target_address, json=json_dict)
            if not r.ok:
                raise HTTPError(403, "Error ecountered while deleting all services. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")

    def setupNetwork (self):
        if upc_mode == "kubernetes":
            # There is no support for setting up networks in Kubernetes right now.
            # However, to allow the same scripts to run on both kubernetes and docker
            # we will not throw any exceptions
            pass
        elif upc_mode == "docker":
            target_address = "{}/create_network".format(self.getSwarmaddr())
            if machines_use_tls:
                r = requests.post(target_address, verify=certificate_bundle_path)
            else:
                r = requests.post(target_address)
            if not r.ok:
                raise HTTPError(403, "Error ecountered setting up the network. Confirm that all machines have running servers.")
        else:
            raise HTTPError(403, "Unknown UPC mode. Reconfigure router with either kubernetes or docker")
        

# Takes in a list of machine tuples, where the first element is the IP_ADDR
# and the second element is the amount of memory available. This creates
# machine objects for each machine with the appropriate weight.
def setupMachines (machines):
    output = []
    total_weight = 0.0
    for weight in machines.values():
        total_weight += weight
    for ip, weight in machines.items():
        output.append(Machine(ip, weight / total_weight))
    return output

# Dictionary consisting of the IP addresses any machines in the cluster
# and their relevant weights.

# Note we are not allowing dynamic addition because we are NOT
# trying to reinvent docker swarm/kubernetes and instead trying
# to construct a cheap replacement

machines = setupMachines (machines_dict) 


# This file should be imported by the controller when not using kubernetes

# Helper function to allocate the Cloud instance
def spawnServiceInstance (service_file, pod_file=None, server_container_name=None):
    num = np.random.rand()
    start = 0.0
    machine = machines[0]
    index = 0
    while num > start:
        start += machines[index].getWeight()
        machine = machines[index]
        index += 1
    return machine.spawnService (service_file, pod_file, server_container_name)

def pauseInstance(name):
    for m in machines:
        if m.pauseService(name):
            return

def resumeInstance(name):
    for m in machines:
        if m.resumeService(name):
            return

def killInstance(name):
    for m in machines:
        if m.killContainer(name):
            return

def clearContainers():
    for m in machines:
        m.clearContainers()

def setupNetworks():
    for m in machines:
        m.setupNetwork()

### Helper functions used in the kubernetes implementation. ###


# Helper function that reads in the givenm json filename and returns 
# a dictionary of the contents
def read_config_json(json_filename):
    with open(json_filename, "r") as json_file:
        return json.load(json_file)

# Takes in a json for a kubernetes configuration and modifies the private port to be
# the given port
def set_service_internal_port(config_json, internal_port):
    config_json['spec']['ports'][0]['targetPort'] = internal_port

def modfiy_pod_port(config_json, server_container_name, container_port):
    containers = config_json['spec']['containers']
    for container in containers:
        if container['name'] == server_container_name:
            container['ports'][0]['containerPort'] = container_port

# Takes in a json for a kubernetes configuration and modifies the broadcasted port
# to become a randomly assigned dynamic port
def modify_config_port(config_json, container_port):
    new_port = np.random.randint (low=30000, high = 32768)
    config_json['spec']['ports'][0]['nodePort'] = new_port
    config_json['spec']['ports'][0]['port'] = new_port
    config_json['spec']['ports'][0]['targetPort'] = container_port
    return new_port

# Takes in a json for a kubernetes configuration and modifies the name to become the
# name passed in.
def modify_name(config_json, new_name):
    config_json['metadata']['name'] = new_name

# Takes in a json for a kubernetes configuration and modifies the label to become the
# name passed in.
def modify_label(config_json, new_label):
    config_json['metadata']['labels']['io.kompose.service'] = new_label

def modify_selector(config_json, new_label):
    config_json['spec']['selector']['io.kompose.service'] = new_label

# Helper function to convert the name produced by temporary files to one accepted by
# kubectl. Also returns the path name for the file
def convert_temp_name(old_name):
    # First remove any "/" and select the last portion
    path_name = old_name.split("/")[-1]
    # Remove any _ by replacing them with -
    new_name = path_name.replace("_", "-")
    # convert all letters to lowercase
    new_name = 'a' + new_name.lower() + 'a'
    return path_name, new_name

# Takes in a configuration that represents the standard file for the system. It modifies
# the listening port to ensure it is correct, adds a random configuration port, changes the
# name and finally launches it as a service using a temporary file. It returns the temporary
# name and the port.
def launch_unique_service(service_config_json, pod_config_json, server_container_name):
        while True:
            with NamedTemporaryFile("w+", dir='.') as new_service_json_file:
                with NamedTemporaryFile("w+", dir='.') as new_pod_json_file:
                    service_path_name, service_name = convert_temp_name(new_service_json_file.name)
                    pod_path_name, pod_name = convert_temp_name(new_pod_json_file.name)
                    # Change the service name
                    modify_name(service_config_json, service_name)
                    # Change the pod name
                    modify_name(pod_config_json, service_name)
                    # Modify the service label
                    modify_label(service_config_json, service_name)
                    # Modify the service selector
                    modify_selector(service_config_json, service_name)
                    # Modify the pod label
                    modify_label(pod_config_json, service_name)
                    # Change the default pod port
                    modfiy_pod_port(pod_config_json, server_container_name, upc_port)
                    # Dump pod file
                    json.dump(pod_config_json, new_pod_json_file)
                    new_pod_json_file.flush()
                    # Port updates need to occur for each failure because they are the
                    # most likely cause
                    new_port = modify_config_port(service_config_json, upc_port)
                    # Dump service file
                    json.dump(service_config_json, new_service_json_file)
                    new_service_json_file.flush()
                    try:
                        # Fix to actually catch errors
                        subprocess.run (['kubectl', 'apply', '-f', '{}'.format (pod_path_name)])
                        subprocess.run (['kubectl', 'apply', '-f', '{}'.format (service_path_name)])
                        # Replace this with a check for if the external address changes
                        subprocess.run(['/bin/bash', 'service_router/pod_wait.sh', '{}'.format(service_name)])
                        return service_name, new_port
                    except:
                        pass

### End of kubernetes helper functions ### 
