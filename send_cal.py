import sys

import Compute_Layer.shared_resources.fake_mongo_types as clsrfmt
import Compute_Layer.shared_resources.ical as clsri

def send_data(calendar_file, pm_addr):
        data = clsri.readCalendarAsEventList(calendar_file)
        db = clsrfmt.CalendarCollection(pm_addr)
        resp = db.insert(data)
        print(resp)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        send_data(sys.argv[1], sys.argv[2])
    else:
        print("Need exactly 2 arguments. Filename and pm address")
