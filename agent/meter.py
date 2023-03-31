
from datetime import datetime, timedelta
import json
import os
import random

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'

def round_time(dt=None, roundTo=60):
   """Round a datetime object to any time lapse in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
   if dt == None : dt = datetime.datetime.now()
   seconds = (dt.replace(tzinfo=None) - dt.min).seconds
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + timedelta(0,rounding-seconds,-dt.microsecond)


def create_metadata():
    with open('data/metadata.json', 'w') as metadata:
        data = {
            'last_updated': None
        }
        json.dump(data, metadata)


def load_metadata():
    with open('data/metadata.json', 'r') as metadata:
        data = json.load(metadata)
    return data


def save_metadata(data):
    with open('data/metadata.json', 'w') as metadata:
        data = json.dump(data, metadata)
    return data


def create_or_get_day(reading_day, empty_day):
    filename = 'data/{}.json'.format(reading_day)
    if not os.path.exists(filename):
        return empty_day
    with open(filename, 'r') as metadata:
        data = json.load(metadata)
    return data


def save_updated_day(reading_day, data):
    filename = 'data/{}.json'.format(reading_day)
    with open(filename, 'w') as metadata:
        data = json.dump(data, metadata)
    return data


def create_or_update_reading(usable_time):
    # 5MS trick : midnight is the correct day, otherwise we need to add 1
    reading_time = usable_time if (usable_time.hour == 0 and usable_time.minute == 0) else usable_time + timedelta(days=1)
    print('updated {} to reading_time {}'.format(usable_time, reading_time))
    reading_day = datetime.strftime(reading_time, DAY_FORMAT)
    empty_day = {
        'reading_day': reading_day
    }
    day = create_or_get_day(reading_day, empty_day)
    reading = random.randint(0, 100) / 10.0
    interval_key = datetime.strftime(usable_time, TIME_FORMAT)
    day[interval_key] = reading
    save_updated_day(reading_day, day)


def tick_completed(config):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/metadata.json'):
        create_metadata()
    metadata = load_metadata()    
    last_updated = metadata['last_updated']
    interval = config['interval_min'] * 60

    ready = False
    if last_updated == None:
        ready = True
    else:
        last_updated_time = datetime.strptime(last_updated, TIME_FORMAT)    
        diff = datetime.now() - last_updated_time
        if diff.total_seconds() > interval:
            ready = True

    if not ready:
        return False
    
    # there is a bit of a gotcha here. I need to record the 5 minute interval (or 30 etc) for this
    # which can only happen every 5 minutes. but I may have gone past this time.
    # for now, I'm going to have a USABLE time which is the 5 minute (or 30 minute) interval before this one
    # ... which I think I shouldn't get a duplicate for (and is OK anyway, as it's keyed)

    usable_time = round_time(datetime.now(), interval)
    print('converted {} to usable time {}'.format(datetime.now(), usable_time))

    create_or_update_reading(usable_time)

    metadata['last_updated'] = datetime.strftime(usable_time, TIME_FORMAT)

    save_metadata(metadata)
    return True

def tick(config):
    if tick_completed(config) == False:
        print('not ready')
        return {
            'status': 'not ready to tick()'
        }

    print("meter ticked at {}".format(datetime.now()))
    return {
        'status': 'tick',
        'now': datetime.strftime(datetime.now(), TIME_FORMAT)
    }


