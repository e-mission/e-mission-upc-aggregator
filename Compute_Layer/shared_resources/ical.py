import datetime
import icalendar
import pytz
import sys

calendarTimeZone = pytz.timezone("US/Pacific")

def createCalendar():
    newCal = icalendar.Calendar()
    newCal.add('prodid', '-//UPC Calender Product//')
    newCal.add('version', '2.0')
    return newCal

# Creates a new event to occur at the given start and endtime, geographic coordinates,
# and the provided attendees. Returns the new event.
def createEvent(startTime, endTime, geo, attendees):
    assert(isinstance(startTime, datetime.datetime))
    assert(isinstance(endTime, datetime.datetime))
    assert(isinstance(geo, tuple))
    assert(len(geo) == 2)
    assert(isinstance(geo[0], float))
    assert(isinstance(geo[1], float))
    assert(isinstance(attendees, list))
    for attendee in attendees:
        assert(isinstance(attendee, str))
    newEvent = icalendar.Event()
    newEvent.add('dtstart', icalendar.prop.vDatetime(startTime))
    newEvent.add('dtend', icalendar.prop.vDatetime(endTime))
    newEvent.add('geo', icalendar.prop.vGeo(geo))
    for attendee in attendees:
        newEvent.add('attendee', icalendar.prop.vCalAddress(attendee))
    newEvent.add('dtstamp', icalendar.prop.vDatetime(datetime.datetime.now(tz=calendarTimeZone)))
    return newEvent

def addEventToCalendar(calendar, event):
    calendar.add_component(event)

# Creates a new event to occur at the given start and endtime, geographic coordinates,
# and the provided attendees. Appends the event to the passed in calendar
def addEventContentsToCalendar(calendar, startTime, endTime, geo, attendees):
    assert isinstance(calendar, icalendar.cal.Calendar)
    addEventToCalendar(calendar, createEvent(startTime, endTime, geo, attendees))

# Writes the icalendar file to given filename
def writeCalendar(filename, calendar):
    calendar = sortEventsByEndTime(calendar)
    with open(filename, "wb") as f:
        f.write(calendar.to_ical())

# Reads the file given by a filename as an icalendar
# file and returns the file.
def readCalendar(filename):
    with open(filename, "rb") as f:
        calendar = icalendar.Calendar.from_ical(f.read())
    return calendar

# Reads a calendar from a file and returns a list of events, where
# each list is a dictionary that can be send to the db over the
# network
def readCalendarAsEventList(filename):
    calendar = readCalendar(filename)
    events = calendar.walk('vevent')
    events_list = []
    for event in events:
        # dict for holding the event
        event_dict = dict()

        # Add metadata
        metadata_dict = dict()
        metadata_dict['type'] = 'calendar'
        event_dict['metadata'] = metadata_dict

        # Add data
        data_dict = dict()
        data_dict['start_time'] = findStartTime(event).isoformat()
        data_dict['end_time'] = findEndTime(event).isoformat()
        data_dict['ts'] = findTimeStamp(event).isoformat()
        data_dict['attendees'] = findAttendees(event)
        data_dict['geo'] = {"type": "Point", "coordinates": findGeo(event)}
        event_dict['data'] = data_dict


        # Append to list
        events_list.append(event_dict)
    return events_list

def findStartTime(event):
    return icalendar.vDatetime.from_ical(event['dtstart'].to_ical())

def findEndTime(event):
    return icalendar.vDatetime.from_ical(event['dtend'].to_ical())

def findTimeStamp(event):
    return icalendar.vDatetime.from_ical(event['dtstamp'].to_ical())

def findAttendees(event):
    attendees = event['attendee']
    attendees_strs = [str(icalendar.vCalAddress.from_ical(attendee.to_ical())) for attendee in attendees]
    return attendees_strs

def findGeo(event):
    return icalendar.vGeo.from_ical(event['geo'].to_ical())


def sortEventsByEndTime(calendar):
    events = calendar.walk('vevent')
    events.sort(key=findEndTime)
    calendar = createCalendar()
    for event in events:
        addEventToCalendar(calendar, event)
    return calendar

# Returns the latest event for the given day. If no event exists for that
# day it returns None.
def returnLatestEvent(calendar, targetDate):
    lastEvent = None
    nextDay = datetime.timedelta(days=1)
    sameDay = datetime.timedelta()
    events = calendar.walk('vevent')
    for event in events:
        endTime = findEndTime(event)
        timeDiff = endTime - targetDate
        if timeDiff >= nextDay:
            return lastEvent
        elif timeDiff > sameDay:
            lastEvent = event
    return lastEvent

intervalAccuracy = datetime.timedelta(minutes=15)
zeroDelta = datetime.timedelta()

def generateRandomDay(earliestStartTime, earliestEndTime, maximumOffset, duration, possibleGeos, attendees):
    events = []
    startTime = earliestStartTime
    while startTime < earliestEndTime:
        event = generateRandomEvent(startTime, maximumOffset, duration, possibleGeos, attendees)
        events.append(event)
        startTime = findEndTime(event)
    return events

def generateRandomEvent(startTime, maximumOffset, duration, possibleGeos, attendees):
    if maximumOffset != zeroDelta:
        startOptions = (maximumOffset // intervalAccuracy) + 1
        startTime = startTime + (np.random.randint(startOptions) * intervalAccuracy)
    endTime = startTime + duration
    geo = possibleGeos[np.random.randint(len(possibleLocations))]
    return createEvent(startTime, endTime, geo, attendees)
