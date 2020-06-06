import requests
import socket
import json
from conf.machine_configs import service_router_tls, service_router_addr, certificate_bundle_path, service_endpoint, pause_endpoint, unpause_endpoint, delete_service_endpoint, delete_all_services_endpoint, setup_network_endpoint

def request_service(service_name):
    json_values = dict()
    json_values['service'] = service_name
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + service_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + service_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
    else:
        data_json = r.json()
        return data_json['address']

def pause_service(address):
    json_entries = dict()
    json_entries['address'] = address
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + pause_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + pause_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
    else:
        # Success
        return True

def resume_service(address):
    json_entries = dict()
    json_entries['address'] = address
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + unpause_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + unpause_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
    else:
        # Success
        return True

def delete_service(address):
    json_entries = dict()
    json_entries['address'] = address
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + delete_service_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + delete_service_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
    else:
        # Success
        return True

def delete_all_services():
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + delete_all_services_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + delete_all_services_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
    else:
        # Success
        return True

# This should only be used as a setup phase when launching the servers
def setup_networks():
    error = False
    try:
        if service_router_tls:
            r = requests.post(service_router_addr + setup_network_endpoint, verify=certificate_bundle_path, timeout=600)
        else:
            r = requests.post(service_router_addr + setup_network_endpoint, timeout=600)
    except (socket.timeout) as e:
        error = True
    #Check if sucessful
    if not r.ok or error:
        error = True
    if error:
        assert(not error)
