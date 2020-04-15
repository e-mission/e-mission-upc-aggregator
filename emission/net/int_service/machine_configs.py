import json

config_file = open('conf/net/machines.json.sample')
config_data = json.load(config_file)
controller_ip = config_data["controller-ip"]
controller_port = int (config_data["controller-port"])
upc_port = int (config_data["upc-port"])
querier_port = int (config_data["upc-port"])
tick_period = float (config_data["tick-period"])
pause_ticks = int (config_data["pause-ticks"])
kill_ticks = int (config_data["kill-ticks"])
swarm_port = int (config_data["swarm-port"])
machines_dict = config_data["machines"]
machines_list = []
for key, value in machines_dict.items ():
    machines_list.append ((key, float (value)))

register_user_endpoint = config_data["register_user_endpoint"]
user_cache_endpoint = config_data["user_cache_endpoint"]
service_endpoint = config_data["service_endpoint"]
cloud_status_endpoint = config_data["cloud_status_endpoint"]
cloud_key_endpoint = config_data["cloud_key_endpoint"]
cloud_profile_endpoint = config_data["cloud_profile_endpoint"]
cloud_aggregate_endpoint = config_data["cloud_aggregate_endpoint"]
query_endpoint = config_data["query_endpoint"]
get_users_endpoint = config_data["get_users_endpoint"]
query_endpoint = config_data["query_endpoint"]
certificate_bundle_path = config_data["certificate_bundle"]

config_file.close ()
