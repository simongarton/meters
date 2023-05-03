
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

# Warning. This might be out of date - everything has moved to meter_pico.py and that has different libraries.

# TODO I should combine these two. the _UTC version is only used on writing out to the file,
# but I think it will work for all uses.

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
TIME_FORMAT_UTC = '%Y-%m-%dT%H:%M:%SZ'
DAY_FORMAT = '%Y-%m-%d'

def round_time(dt=None, roundTo=60):
    """Round a datetime object to any time lapse in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if dt == None : dt = datetime.datetime.utcnow()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    return dt + timedelta(0,rounding-seconds,-dt.microsecond)


def create_metadata():
    with open('data/metadata.json', 'w') as metadata:
        data = {
            'last_updated': None,
            'last_uploaded': None,
        }
        json.dump(data, metadata, indent=4)


def load_metadata():
    with open('data/metadata.json', 'r') as metadata:
        data = json.load(metadata)
    return data


def save_metadata(data):
    with open('data/metadata.json', 'w') as metadata:
        data = json.dump(data, metadata, indent=4)
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
    with open(filename, 'r') as payload:
        data = json.load(payload)
    return data


def save_updated_day(reading_day, data):
    filename = 'data/{}.json'.format(reading_day)
    with open(filename, 'w') as metadata:
        data = json.dump(data, metadata, indent=4)
    return data


def map_timestamp_to_reading_day(working_timestamp):
    # 5MS trick : midnight is the correct day, otherwise we need to add 1
    reading_day = working_timestamp if (working_timestamp.hour == 0 and working_timestamp.minute == 0) else working_timestamp + timedelta(days=1)
    reading_day = reading_day.replace(hour=0, minute= 0)
    # print('updated {} to reading_time {}'.format(working_timestamp, reading_day))
    return reading_day


def generate_reading(usable_time, config, channel_factor):
    working_hour = usable_time.hour
    profile_data = config['profile'] if 'profile' in config else {}
    profile_value = profile_data[str(working_hour)] if str(working_hour) in profile_data else 1
    variability = config['variability'] if 'variability' in config else 0
    reading = profile_value
    varied_reading = reading + (random.uniform(0, variability) * reading) - (2 * random.uniform(0, variability) * reading) 
    channel_reading = round(varied_reading * channel_factor, 3)
    return channel_reading if channel_reading > 0 else 0
        

def create_or_get_snapshot_block(config, metadata):
    channel_data = config['channels'] if 'channels' in config else {"Total":1.0}
    snapshot_data = metadata['snapshots'] if 'snapshots' in metadata else {}
    snapshot_block = {}
    for channel_name, channel_factor in channel_data.items():
        snapshot_value = snapshot_data[channel_name] if channel_name in snapshot_data else 0
        snapshot_block[channel_name] = snapshot_value
    return snapshot_block    
 

def build_datastream_block(channel_data):
    datastream_block = {}
    for channel_name, channel_factor in channel_data.items():
        datastream_block[channel_name] = {}
    return datastream_block


def create_or_update_readings(usable_time, serial, config, snapshot_block):
    updated_snapshot_block = snapshot_block.copy()
    reading_time =  map_timestamp_to_reading_day(usable_time)
    reading_day = datetime.strftime(reading_time, DAY_FORMAT)
    channel_data = config['channels'] if 'channels' in config else {"Total":1.0}
    datastream_block = build_datastream_block(channel_data)
    empty_day = {
        'serial': serial,
        'reading_day': reading_day,
        'snapshots': snapshot_block,
        'datastreams': datastream_block,
    }

    day = create_or_get_day(reading_day, empty_day)

    for channel_name, channel_factor in channel_data.items():
        reading = generate_reading(usable_time, config, channel_factor)
        interval_key = datetime.strftime(usable_time, TIME_FORMAT_UTC)
        day['datastreams'][channel_name][interval_key] = reading
        updated_snapshot_block[channel_name] = updated_snapshot_block[channel_name] + reading
    save_updated_day(reading_day, day)
    return updated_snapshot_block


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
        print('no data to load for {} at {}'.format(reading_day, datetime.utcnow()))
        return False
    # print('got data to load for {} at {}'.format(reading_day, datetime.utcnow()))
    url = config['tempest_url']
    response = requests.post(url + 'update', json=day_data)
    return True


def upload_completed(config):
    metadata = create_or_load_metadata()   
    interval = config['interval_min'] * 60 
    usable_time = round_time(datetime.utcnow(), interval)
    current_day = datetime.strftime(map_timestamp_to_reading_day(usable_time), DAY_FORMAT)
    current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
    if current_day_file == None or current_day != current_day_file:
        # print('need to upload file as current_day is {} but working file is {}'.format(current_day, current_day_file))
        # I actually upload the file each time - but leave this logic here in case I take it out again, or if
        # one of those uplaods fails.
        if upload_file(current_day_file, config):
            # print("uploaded file worked, updating metadata to {}".format(current_day))
            metadata['last_uploaded'] = datetime.strftime(datetime.utcnow(), TIME_FORMAT)
            metadata['current_day_file'] = current_day
            save_metadata(metadata)
        else:
            print("uploaded file didn't work, updating metadata to {}".format(current_day))
            metadata['current_day_file'] = current_day
            save_metadata(metadata)
        return True
    # print('no need to upload file as current_day is {} and working file is also {}'.format(current_day, current_day_file))
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
        diff = datetime.utcnow() - last_updated_time
        if diff.total_seconds() > interval:
            ready = True

    if not ready:
        return False
    
    # there is a bit of a gotcha here. I need to record the 5 minute interval (or 30 etc) for this
    # which can only happen every 5 minutes. but I may have gone past this time.
    # for now, I'm going to have a USABLE time which is the 5 minute (or 30 minute) interval before this one
    # ... which I think I shouldn't get a duplicate for (and is OK anyway, as it's keyed)

    usable_time = round_time(datetime.utcnow(), interval)
    # print('converted {} to usable time {}'.format(datetime.utcnow(), usable_time))

    save_reading_for_time(usable_time, config, metadata)


def save_reading_for_time(usable_time, config, metadata):    

    snapshot_block = create_or_get_snapshot_block(config, metadata)

    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    updated_snapshot_block = create_or_update_readings(usable_time, serial, config, snapshot_block)

    metadata['snapshots'] = updated_snapshot_block
    metadata['last_updated'] = datetime.strftime(usable_time, TIME_FORMAT)

    save_metadata(metadata)
    return True


def heartbeat(config):
    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    ip = config['ip'] if 'ip' in config else 'no-ip'
    heartbeat_data = {
        'serial': serial,
        'ip': ip,
        'timestamp': datetime.strftime(datetime.utcnow(), TIME_FORMAT)
    }
    url = config['tempest_url']
    response = requests.post(url + 'heartbeat', json=heartbeat_data)


def tick(config):
    status = ''
    # run a tick (if ready) to store some more 5min data
    if tick_completed(config) == False:
        status = status + 'not ready to tick. '
    else:
        # upload the current file anyway
        metadata = create_or_load_metadata()   
        current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
        if current_day_file:    
            upload_file(current_day_file, config)
            status = status + 'partial file uploaded. '
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
        'now': datetime.strftime(datetime.utcnow(), TIME_FORMAT)
    }


def get_day(day):
    # another 5MS hack - today is actually yesterday
    day = day if day is not None else datetime.strftime(datetime.utcnow() + timedelta(days=1), DAY_FORMAT)
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


def generate_days(start_day, n):
    config = load_config()
    serial = config['serial']

    for day in range(0, n):
        working_day = datetime.strptime(start_day, DAY_FORMAT) + timedelta(days=day)
        generate_day(datetime.strftime(working_day, DAY_FORMAT))
        data = get_day_data(datetime.strftime(working_day, DAY_FORMAT))


def generate_day(reading_day):
    config = load_config()
    interval = config['interval_min']

    working_day = datetime.strptime(reading_day, DAY_FORMAT) + timedelta(days=-1)
    start_day = working_day.day

    print('creating day for {}'.format(reading_day))

    while working_day.day == start_day:
        # 5MS start at 5 past midnight
        working_day = working_day + timedelta(minutes=interval)
        # I think I have to do this each time
        metadata = create_or_load_metadata()   
        save_reading_for_time(working_day, config, metadata)
    

# I need this as I run this script from a cron job
if __name__ == '__main__':
    # for running from a cron job - cold as there is no config loaded, and tick requires it
    cold_tick()
    
    # to generate some days of history
    # generate_days('2023-03-05', 31)
