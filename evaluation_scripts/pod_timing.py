import argparse
import json
import time
import subprocess
from tempfile import NamedTemporaryFile
from Compute_Layer.Service_Router.swarm import read_config_json, convert_temp_name, modify_name, modify_label


def pm_test():
    pod_file = "kubernetes/web-server-pod.json"
    pod_name = "web-server"
    return pod_tests(pod_file, pod_name)

def calendar_test():
    pod_file = "kubernetes/calendar-pod.json"
    pod_name = "calendar"
    return pod_tests(pod_file, pod_name)

def pipeline_test():
    pod_file = "kubernetes/pipeline-pod.json"
    pod_name = "pipeline"
    return pod_tests(pod_file, pod_name)

def pod_tests(pod_file, pod_name):
    trials = dict()
    trials[0] = pod_test(pod_file, pod_name, 0)
    trials[25] = pod_test(pod_file, pod_name, 25)
    trials[50] = pod_test(pod_file, pod_name, 50)
    return trials

def pod_test(pod_file, pod_name, num_other_pods):
    # Fill in other pods
    fake_names = generate_dummy_pods(num_other_pods)
    
    # Switch num_trials to 50
    num_trials = 2
    times = []
    for i in range(num_trials):
        times.append(time_pod_startup(pod_file, pod_name))
        delete_pod(pod_name)

    # Delete other pods
    delete_dummy_pods(fake_names)

    return times
    
def generate_dummy_pods(num_pods):
    base_pod = "kubernetes/db-pod.json"
    names = []
    if num_pods > 0:
        pod_config_json = read_config_json(base_pod)
    for i in range(num_pods):
        with NamedTemporaryFile("w+", dir='.') as new_pod_file:
            pod_path_name, pod_name = convert_temp_name(new_pod_file.name)
            modify_name(pod_config_json, pod_name)
            # Modify the pod label
            modify_label(pod_config_json, pod_name)
            # Dump pod file
            json.dump(pod_config_json, new_pod_file)
            new_pod_file.flush()
            subprocess.run (['kubectl', 'apply', '-f', '{}'.format (pod_path_name)])
            names.append(pod_name)
    for name in names:
        subprocess.run(['/bin/bash', 'kubernetes/pod_wait.sh', '{}'.format(name)])
    return names

def delete_dummy_pods(names):
    subprocess.run(["kubectl", "delete", "--all", "pods" ,"--namespace=default"])

def time_pod_startup(pod_file, pod_name):
    start_time = time.time()
    subprocess.run (['kubectl', 'apply', '-f', '{}'.format (pod_file)])
    # Add a check for the pod saying running
    subprocess.run(['/bin/bash', 'kubernetes/pod_wait.sh', '{}'.format(pod_name)])
    end_time = time.time()
    return end_time - start_time

def delete_pod(pod_name):
    subprocess.run (['kubectl', 'delete', 'pod', '{}'.format(pod_name)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file", type=str,
        help="Name of the output json_file")
    args = parser.parse_args()
    json_values = dict()
    json_values["pm"] = pm_test()
    json_values["calendar"] = calendar_test()
    json_values["pipeline"] = pipeline_test()
    with open(args.output_file, "w") as f:
        f.write(json.dumps(json_values, indent=4))
