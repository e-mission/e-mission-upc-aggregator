import argparse
import json
import time
import Compute_Layer.shared_resources.fake_mongo_types as clsrfmt


def pm_test():
    pod_name = "PM"
    return pod_tests(pod_name)

def calendar_test():
    pod_name = "Calendar"
    return pod_tests(pod_name)

def pipeline_test():
    pod_name = "Pipeline"
    return pod_tests(pod_name)

def pod_tests(pod_name):
    trials = dict()
    trials[0] = pod_test(pod_name, 0)
    trials[10] = pod_test(pod_name, 10)
    trials[20] = pod_test(pod_name, 20)
    return trials

def pod_test(pod_name, num_other_pods):
    # Fill in other pods
    fake_names = generate_dummy_pods(num_other_pods)
    
    num_trials = 20
    times = []
    for i in range(num_trials):
        address, time_val = time_pod_startup(pod_name)
        times.append(time_val)
        clsrfmt.delete_service(address)

    # Delete other pods
    delete_dummy_pods(fake_names)
    return times
    
def generate_dummy_pods(num_pods):
    dummy_name = "db"
    addresses = []
    for i in range(num_pods):
        addresses.append(clsrfmt.request_service(dummy_name))
    return addresses

def delete_dummy_pods(names):
    clsrfmt.delete_all_services()

def time_pod_startup(pod_name):
    start_time = time.time()
    address = clsrfmt.request_service(pod_name)
    end_time = time.time()
    return address, end_time - start_time

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
