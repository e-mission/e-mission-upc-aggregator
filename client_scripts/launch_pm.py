import argparse
from shared_apis.service_router_api import request_service
from shared_apis.fake_mongo_types import upload_secret_key

def launch_pm(secret_key):
    # Get the PM address
    pm_address = request_service("PM")

    # Upload the secret key
    upload_secret_key(pm_address, secret_key)

    # Output the pm_address
    print(pm_address)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
            Example script to run all the example script steps
            ''')
    parser.add_argument("secret_key", type=str,
        help='''
            the secret key used to encrypt user data
        ''')
    args = parser.parse_args()
    launch_pm(args.secret_key)
