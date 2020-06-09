import argparse
import json
import bson.json_util as bju
import pymongo
from shared_apis.index_classes import UsercacheCollection

def save_server_to_phone(output_file, uuid, pm_address):
    # Load the index file
    usercache_db = UsercacheCollection(pm_address)
    # Load the data from the PM
    retrievedData = list(usercache_db.find({"user_id": uuid, "metadata.type": "document"}, # query
                                            {'_id': False, 'user_id': False}).sort("metadata.write_ts", pymongo.ASCENDING)) # projection, sort
    # Store the data in the file
    json.dump(retrievedData, open(output_file, "w"), default=bju.default, allow_nan=False, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            downloads data from an existing pm in json format. A consist uuid must be used
            to track user data, but this should eventually be removed.
            ''')
    parser.add_argument("output_file", type=str,
        help='''
            the output json file for the user
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
    save_server_to_phone(args.output_file, args.uuid, args.pm_address)
