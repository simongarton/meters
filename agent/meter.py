
from datetime import datetime, timedelta
import json
import os
import random
import requests

#
# meter.py
#
# the main logic for a meter - generating values and storing them.
#
# to do :
# - clean up old files ? but I need history so no
# - datastreams
# - snapshots
# - logging to log files, not terminal - can then query with agent
# - sensible profiles

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
            'last_updated': None,
            'last_uploaded': None,
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


def get_day_data(reading_day):
    filename = 'data/{}.json'.format(reading_day)
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as metadata:
        data = json.load(metadata)
    return data


def save_updated_day(reading_day, data):
    filename = 'data/{}.json'.format(reading_day)
    with open(filename, 'w') as metadata:
        data = json.dump(data, metadata)
    return data


def create_or_update_reading(usable_time, serial):
    # 5MS trick : midnight is the correct day, otherwise we need to add 1
    reading_time = usable_time if (usable_time.hour == 0 and usable_time.minute == 0) else usable_time + timedelta(days=1)
    print('updated {} to reading_time {}'.format(usable_time, reading_time))
    reading_day = datetime.strftime(reading_time, DAY_FORMAT)
    empty_day = {
        'serial': serial,
        'reading_day': reading_day
    }
    day = create_or_get_day(reading_day, empty_day)
    reading = random.randint(0, 100) / 10.0
    interval_key = datetime.strftime(usable_time, TIME_FORMAT)
    day[interval_key] = reading
    save_updated_day(reading_day, day)


def create_or_load_metadata():
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/metadata.json'):
        create_metadata()
    metadata = load_metadata()    
    return metadata


def upload_yesterdays_file(config):
    # 5MS - yesterday's file has today's date, doh.
    reading_day = datetime.strftime(datetime.now() + timedelta(days=0), DAY_FORMAT)
    return upload_file(reading_day, config)


def upload_file(reading_day, config):
    day_data = get_day_data(reading_day)
    if day_data == None:
        print('no data to load for {} at {}'.format(reading_day, datetime.now()))
        return False
    print('got data to load for {} at {}'.format(reading_day, datetime.now()))
    print(day_data)
    url = config['tempest_url']
    response = requests.post(url + 'update', json=day_data)
    print(response)
    return True


def upload_completed(config):
    metadata = create_or_load_metadata()    
    last_uploaded = metadata['last_uploaded']
    if last_uploaded == None:
        if upload_yesterdays_file(config):
            metadata['last_uploaded'] = datetime.strftime(datetime.now(), TIME_FORMAT)
            save_metadata(metadata)
        return True
    last_uploaded_time = datetime.strptime(last_uploaded, TIME_FORMAT)
    diff = datetime.now() - last_uploaded_time
    if diff.total_seconds() > 24 * 60 * 60:
        if upload_yesterdays_file(config):
            metadata['last_uploaded'] = datetime.strftime(datetime.now(), TIME_FORMAT)
            save_metadata(metadata)
        return True
    return False


def tick_completed(config):
    metadata = create_or_load_metadata()    
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

    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    create_or_update_reading(usable_time, serial)

    metadata['last_updated'] = datetime.strftime(usable_time, TIME_FORMAT)

    save_metadata(metadata)
    return True

def heartbeat(config):
    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    ip = config['ip'] if 'ip' in config else 'no-ip'
    heartbeat_data = {
        'serial': serial,
        'ip': ip,
        'timestamp': datetime.strftime(datetime.now(), TIME_FORMAT)
    }
    url = config['tempest_url']
    response = requests.post(url + 'heartbeat', json=heartbeat_data)


def tick(config):
    status = ''
    if tick_completed(config) == False:
        status = status + 'not ready to tick. '
    else:
        status = status + 'tick completed. '

    if upload_completed(config) == False:
        status = status + 'not ready to upload. '
    else:
        status = status + 'upload completed. '

    heartbeat(config)

    return {
        'status': status,
        'now': datetime.strftime(datetime.now(), TIME_FORMAT)
    }


def get_day(day):
    # another 5MS hack - today is actually yesterday
    day = day if day is not None else datetime.strftime(datetime.now() + timedelta(days=1), DAY_FORMAT)
    return get_day_data(day)
    

def upload_day(day, config):
    return upload_file(day, config)

def redial(from_day, config):
    # TBC - count the number of payloads I actually redial
    return 0