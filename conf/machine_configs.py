import json

config_file = open('conf/machines.json.sample')
config_data = json.load(config_file)

# Setup the service router
service_router_tls = config_data["service_router_use_tls"]
service_router_ip = config_data["service_router_ip"]
service_router_port = config_data["service_router_port"]
if service_router_tls:
    service_router_addr = "https://{}:{}".format(service_router_ip, service_router_port)
else:
    service_router_addr = "http://{}:{}".format(service_router_ip, service_router_port)
service_endpoint = config_data["service_endpoint"]
pause_endpoint = config_data["pause_endpoint"]
unpause_endpoint = config_data["unpause_endpoint"]
delete_service_endpoint = config_data["delete_service_endpoint"]
delete_all_services_endpoint = config_data["delete_all_services_endpoint"]
setup_network_endpoint = config_data["setup_network_endpoint"]

# Setup the machines in the cluster
machines_use_tls = config_data['machines_use_tls']
certificate_bundle_path = config_data["certificate_bundle_path"]
base_machines_dict = config_data["machines"]
machines_dict = dict()
for ip, weight in base_machines_dict.items():
    if machines_use_tls:
        machine_addr = "https://{}".format(ip)
    else:
        machine_addr = "http://{}".format(ip)
    machines_dict[machine_addr] = weight

upc_port = config_data["upc_port"]
swarm_port = config_data["swarm_port"]

# API endpoints
insert_endpoint = config_data["insert_endpoint"]
insert_deprecated_endpoint = config_data["insert_deprecated_endpoint"]
find_endpoint = config_data["find_endpoint"]
find_one_endpoint = config_data["find_one_endpoint"]
delete_endpoint = config_data["delete_endpoint"]
update_endpoint = config_data["update_endpoint"]
update_deprecated_endpoint = config_data["update_deprecated_endpoint"]
replace_one_endpoint = config_data["replace_one_endpoint"]
count_endpoint = config_data["count_endpoint"]
distinct_endpoint = config_data["distinct_endpoint"]
cloud_key_endpoint = config_data["cloud_key_endpoint"]
privacy_budget_endpoint = config_data["privacy_budget_endpoint"]


upc_mode = config_data["upc_mode"]

config_file.close ()
