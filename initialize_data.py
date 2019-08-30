import subprocess
import argparse

def main (user_count, trip_count):
    ret = subprocess.Popen (["./e-mission-py.bash", "emission/simulation/simulate_fake_users.py", user_count, trip_count], cwd="./")
    ret.wait ()

if __name__ == "__main__":
    parser = argparse.ArgumentParser (description="Script to generate a number of fake users and sync their data to their respective user clouds")
    parser.add_argument ("user_count", type=int,
            help="Number of users to be created")
    parser.add_argument ("trip_count", type=int,
            help="Number of trips taken by each user")
    items = parser.parse_args ()
    main (str (items.user_count), str (items.trip_count))
