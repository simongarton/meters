
from datetime import datetime, timedelta
import json
import os
import random
import requests
import socket

#
# meter.py
#
# the main logic for a meter - generating values and storing them.
#


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


def map_timestamp_to_reading_day(working_timestamp):
    # 5MS trick : midnight is the correct day, otherwise we need to add 1
    reading_day = working_timestamp if (working_timestamp.hour == 0 and working_timestamp.minute == 0) else working_timestamp + timedelta(days=1)
    reading_day = reading_day.replace(hour=0, minute= 0)
    print('updated {} to reading_time {}'.format(working_timestamp, reading_day))
    return reading_day


def create_or_update_reading(usable_time, serial):
    reading_time =  map_timestamp_to_reading_day(usable_time)
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


def upload_file(reading_day, config):
    if reading_day == None:
        return True
    day_data = get_day_data(reading_day)
    if day_data == None:
        print('no data to load for {} at {}'.format(reading_day, datetime.now()))
        return False
    print('got data to load for {} at {}'.format(reading_day, datetime.now()))
    url = config['tempest_url']
    response = requests.post(url + 'update', json=day_data)
    return True


def upload_completed(config):
    metadata = create_or_load_metadata()   
    interval = config['interval_min'] * 60 
    usable_time = round_time(datetime.now(), interval)
    current_day = datetime.strftime(map_timestamp_to_reading_day(usable_time), DAY_FORMAT)
    current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
    if current_day_file == None or current_day != current_day_file:
        print('need to upload file as current_day is {} but working file is {}'.format(current_day, current_day_file))
        if upload_file(current_day_file, config):
            metadata['last_uploaded'] = datetime.strftime(datetime.now(), TIME_FORMAT)
            metadata['current_day_file'] = current_day
            save_metadata(metadata)
        return True
    print('no need to upload file as current_day is {} and working file is also {}'.format(current_day, current_day_file))
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
    # run a tick (if ready) to store some more 5min data
    if tick_completed(config) == False:
        status = status + 'not ready to tick. '
    else:
        status = status + 'tick completed. '

    # check to see if the PREVIOUS file that I was writing to has been uploaded
    # each time I run this, I look at the current date I'm writing to and the last file
    # I wrote to - in metadata. if they are not the same, upload the last file (as it's complete)
    # and update the file
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


def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    data['ip'] = get_ip()
    return data


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def cold_tick():
    config = load_config()
    tick(config)
    

# I need this as I run this script from a cron job
if __name__ == '__main__':
    cold_tick()
