import argparse
import json
import numpy as np
import subprocess
import shared_apis.service_router_api as sasra
import shared_apis.queries as saq

def main(input_dir, query_file, output_file):
    files = os.listdir(input_dir)
    count_results = []
    for filename in files:
        input_file = input_dir + "/" + filename
        secret_key = np.random.randint(low=0, high=1 << 62, type='uint64')
        res = subprocess.run(["./e-mission-py.bash", "client_scripts/full_count_metrics.py", 
            input_file, query_file, secret_key], capture_output=True, encoding="utf-8")
        count_result = res.stdout.strip()
        count_results.append(json.loads(count_result))
    num_participants = 0
    total = 0
    for result in count_results:
        if result['success']:
            num_participants += 1
            total += result['results']

    with open(query_file, "r") as f:
        query_contents = json.load(f)
    offset = query_contents['query']['offset']
    alpha = query_contents['query']['alpha']
    query_contents = saq.AE(1)
    noisy_result = query_contents.produce_noisy_result (total, alpha, offset)
    output = dict()
    output['number_participants'] = num_participants
    output['actual_total'] = total
    output['noisy_total'] = noisy_result
    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            Example script to run all the example script steps
            ''')
    parse.add_argument("input_dir", type=str,
        help='''
            the input json file for the user
        ''')
    parse.add_argument("query_file", type=str,
        help='''
            the input file for the user's query
        ''')
    parse.add_argument("output_file", type=str,
        help='''
            the output json file for the reuslts
        ''')
    args = parser.parse_args()
    main(args.input_file, args.query_file, args.output_file)
