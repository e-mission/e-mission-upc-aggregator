import sys
import requests
import json
import datetime
import pytz

def use_find_last(pm_addr, cal_addr):
    json_dict = dict()
    tz_info = pytz.timezone("US/Pacific")
    json_dict['date'] = datetime.datetime(2020, 3, 15, tzinfo=tz_info).isoformat()
    json_dict['pm_address'] = pm_addr
    r = requests.post("{}/get_last_event".format(cal_addr), json=json_dict)
    results = r.json()
    print(results)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        use_find_last(sys.argv[1], sys.argv[2])
    else:
        print("This takes two argument, the pm addr and cal addr")
