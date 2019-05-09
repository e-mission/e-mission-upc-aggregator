from emission.simulation.client import EmissionFakeDataGenerator
from emission.simulation.fake_user import FakeUser

def create_and_sync_data (userlist, numTrips):
    measurements = []
    for i in range (len (userlist)):
        user_measurements = []
        for _ in range (numTrips):
            temp = userlist[i].take_trip ()
            print('# of location measurements:', len(temp))
            user_measurements.append (temp)
        print('Path:', userlist[i]._path)

    for i in range (len (userlist)):
        print (len (userlist[i]._measurements_cache))
        userlist[i].sync_data_to_server ()
        print (len (userlist[i]._measurements_cache))
