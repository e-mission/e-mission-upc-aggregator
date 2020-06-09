import argparse
import json
from past.utils import old_div
from shared_apis.index_classes import UsercacheCollection

def isMillisecs(ts):
  return not (ts < 10 ** 11)

def save_phone_to_server(input_file, uuid, pm_address):
    # Load the entries from the input_json 
    with open(input_file) as fp:
        entries = json.load(fp)

    # Get the index to upload
    usercache_db = UsercacheCollection(pm_address)

    for data in entries:
        # Format the data to match server expectations
        del data["_id"]
        if 'write_local_dt' in data['metadata']:
            del data['metadata']['write_local_dt']
        if 'type' not in data['metadata']:
            data['metadata']['type'] = "sensor-data"
        data.update({"user_id": uuid})
        # Hack to deal with milliseconds until we have moved everything over
        if isMillisecs(data["metadata"]["write_ts"]):
            data["metadata"]["write_ts"] = old_div(float(data["metadata"]["write_ts"]), 1000)

        if "ts" in data["data"] and isMillisecs(data["data"]["ts"]):
            data["data"]["ts"] = old_div(float(data["data"]["ts"]), 1000)

       # Upload the data to the pm
        document = {'$set': data}
        update_query = {'user_id': uuid,
                        'metadata.type': data["metadata"]["type"],
                        'metadata.write_ts': data["metadata"]["write_ts"],
                        'metadata.key': data["metadata"]["key"]}
        result = usercache_db.update_one(update_query,
                                           document,
                                           upsert=True)
        # I am not sure how to trigger a writer error to test this
        # and whether this is the format expected from the server in the rawResult
        if 'ok' in result.raw_result and result.raw_result['ok'] != 1.0:
            raise Exception()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            uploads data in a json format to an existing PM. A consist uuid must be used
            to track user data, but this should eventually be removed.
            ''')
    parser.add_argument("input_file", type=str,
        help='''
            the input json file for the user
        ''')
    parser.add_argument("uuid", type=str,
        help='''
            the uuid used to tag all of the user's records. This should eventually be removed
        ''')
    parser.add_argument("pm_address", type=str,
        help='''
            address of an existing pm. This pm is the target upload location
        ''')
    args = parser.parse_args()
    save_phone_to_server(args.input_file, args.uuid, args.pm_address)
