
import time
import json
import random
import urequests
import network
import secrets

#
# meter_light.py
#
# the main logic for a meter - generating values and storing them. this is essentially the same
# as the main meter.py, but with datetime, requests and socket imports removed - not available on my
# Pico H (which has no wifi connectivity.)
#
# https://docs.python.org/3/library/time.html#module-time
# https://www.programiz.com/python-programming/time

# With time, I can do the following
# time.localtime() - returns a struct/tuple with the current time
# time.gmtime() - returns a struct/tuple in UTC. consider making EVERYTHING UTC as InfluxDB will want it.
# time.time() - a float, number of seconds since epoch
# time.localtime(n) - returns a struct/tuple based on N the number of seconds since epoch
# time.gmtime(n) - returns a struct/tuple based on N the number of seconds since epoch
# time.mktime(struct) - turns the struc into the number of seconds since epoch
# time.strptime('04/02/2023, 16:07:46', '%m/%d/%Y, %H:%M:%S') - get a struct from a string
# time.strftime("%m/%d/%Y, %H:%M:%S", n) - turns a struct into a string

# with strptime, strftime : the bloody T in the middle isn't supported. so make it a space

# if I'm using a time, make it the struct

# Also need to change requests to urequests; network instead of socket.

# OFFS, os.path isn't implemented.
# I use it in 3 places to see if a file or directory exists.
# there is this, but mip doesn't install it : https://github.com/micropython/micropython-lib
# write my own file_exists() and create the dir anyway - TBC

# OK, we can't pretty print json, no indent.

# OFFS ** 2, on my laptop time.localtime() returns a struct; on the pi it returns a tuple.
# tm_year = 0, tm_mon = 1, tm_day = 2, tm_hour = 3, tm_min = 4, tm_sec = 5, tm_wday = 6, tm_yday = 7 and no DST.

# OFFS once more, have to write strftime, and strptime - not supported on MicroPython.
# only one strptime(); 8 x strftime() and remember it's a damn tuple.

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'

def round_time(dt=None, roundTo=60):
    # pass in the struct
    if dt == None : dt = time.localtime()
    seconds = time.mktime(dt)
    remainder = seconds % roundTo
    return time.localtime(seconds - remainder)


def strftime_time(struct_time):
    # assume I'm using '%Y-%m-%d %H:%M:%S'
    return "{:04.0f}-{:02.0f}-{:02.0f} {:02.0f}:{:02.0f}:{:02.0f} ".format(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], )

def strftime_day(struct_time):
    # assume I'm using '%Y-%m-%d'
    return "{:04.0f}-{:02.0f}-{:02.0f}".format(struct_time[0], struct_time[1], struct_time[2])

def strptime_time(struct_time_string):
    # assume I'm using '%Y-%m-%d %H:%M:%S'
    year = int(struct_time_string[:4])
    month = int(struct_time_string[5:7])
    day = int(struct_time_string[8:10])
    hour = int(struct_time_string[11:13])
    min = int(struct_time_string[14:16])
    sec = int(struct_time_string[17:19])
    return time.mktime((year, month, day, hour, min, sec, 1, 1))


def seconds_between(later, earlier):
    later_seconds = time.mktime(later)
    earlier_seconds = time.mktime(earlier)
    return later_seconds - earlier_seconds


def add_delta(time_struct, years=None, days=None, hours=None, minutes=None, seconds=None):
    current_seconds = time.mktime(time_struct)
    if years:
        current_seconds = current_seconds + (years * 365 * 24 * 60 * 60)
    if days:
        current_seconds = current_seconds + (days * 24 * 60 * 60)
    if hours:
        current_seconds = current_seconds + (hours * 60 * 60)    
    if minutes:
        current_seconds = current_seconds + (minutes * 60)    
    if seconds:
        current_seconds = current_seconds + (seconds)    
    return time.localtime(current_seconds)


def round_to_whole_day(time_struct):
    current_seconds = time.mktime(time_struct)
    delta_hour = time_struct[3] * 60 * 60
    delta_minute = time_struct[4] * 60
    delta_second = time_struct[5]
    rounded_seconds = current_seconds - delta_hour - delta_minute - delta_second
    return time.localtime(rounded_seconds) 


def file_exists(filename):
    try:
        with open(filename, 'r') as file:
            pass
        return True
    except:
        return False
    

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
    if not file_exists(filename):
        return empty_day
    with open(filename, 'r') as metadata:
        data = json.load(metadata)
    return data


def get_day_data(reading_day):
    filename = 'data/{}.json'.format(reading_day)
    if not file_exists(filename):
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
    reading_day = working_timestamp if (working_timestamp[3] == 0 and working_timestamp[4] == 0) else add_delta(working_timestamp, days=1)
    reading_day = round_to_whole_day(reading_day)
    # print('updated {} to reading_time {}'.format(working_timestamp, reading_day))
    return reading_day


def generate_reading(usable_time, config, channel_factor):
    working_hour = usable_time[3]
    profile_data = config['profile'] if 'profile' in config else {}
    profile_value = profile_data[str(working_hour)] if str(working_hour) in profile_data else 1
    variability = config['variability'] if 'variability' in config else 0
    reading = random.randint(0, profile_value * 10) / 10.0
    varied_reading = reading + (random.uniform(0, variability) * reading) - (2 * random.uniform(0, variability) * reading) 
    channel_reading = round(varied_reading * channel_factor, 3)
    return channel_reading
        

def create_or_get_snapshot_block(config, metadata):
    channel_data = config['channels'] if 'channels' in config else {"PositiveActiveEnergyTotal":1.0}
    snapshot_data = metadata['snapshots'] if 'snapshots' in config else {}
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
    reading_day = strftime_day(reading_time)
    channel_data = config['channels'] if 'channels' in config else {"PositiveActiveEnergyTotal":1.0}
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
        interval_key = strftime_time(usable_time)
        day['datastreams'][channel_name][interval_key] = reading
        updated_snapshot_block[channel_name] = updated_snapshot_block[channel_name] + reading
    save_updated_day(reading_day, day)
    return updated_snapshot_block


def create_or_load_metadata():
    if not file_exists('data/metadata.json'):
        create_metadata()
    metadata = load_metadata()    
    return metadata


def upload_file(reading_day, config):
    if reading_day == None:
        return True
    day_data = get_day_data(reading_day)
    if day_data == None:
        print('no data to load for {} at {}'.format(reading_day, time.localtime()))
        return False
    # print('got data to load for {} at {}'.format(reading_day, time.localtime()))
    url = config['tempest_url']
    response = urequests.post(url + 'update', json=day_data)
    return True


def upload_completed(config):
    metadata = create_or_load_metadata()   
    interval = config['interval_min'] * 60 
    usable_time = round_time(time.localtime(), interval)
    current_day = strftime_day(map_timestamp_to_reading_day(usable_time))
    current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
    if current_day_file == None or current_day != current_day_file:
        # print('need to upload file as current_day is {} but working file is {}'.format(current_day, current_day_file))
        if upload_file(current_day_file, config):
            # print("uploaded file worked, updating metadata to {}".format(current_day))
            metadata['last_uploaded'] = strftime_time(time.localtime())
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
        last_updated_time = time.localtime(strptime_time(last_updated))
        diff = seconds_between(time.localtime(), last_updated_time)    
        if diff > interval:
            ready = True

    if not ready:
        return False
    
    # there is a bit of a gotcha here. I need to record the 5 minute interval (or 30 etc) for this
    # which can only happen every 5 minutes. but I may have gone past this time.
    # for now, I'm going to have a USABLE time which is the 5 minute (or 30 minute) interval before this one
    # ... which I think I shouldn't get a duplicate for (and is OK anyway, as it's keyed)

    usable_time = round_time(time.localtime(), interval)
    # print('converted {} to usable time {}'.format(datetime.now(), usable_time))

    snapshot_block = create_or_get_snapshot_block(config, metadata)

    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    updated_snapshot_block = create_or_update_readings(usable_time, serial, config, snapshot_block)

    metadata['snapshots'] = updated_snapshot_block
    metadata['last_updated'] = strftime_time(usable_time)

    save_metadata(metadata)
    return True


def connect():
    print('connecting to {}'.format(secrets.SSID))
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.SSID, secrets.PASSWORD)
    print('connected to wifi : {}'.format(wlan.isconnected()))


def heartbeat(config):
    connect()
    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    ip = config['ip'] if 'ip' in config else 'no-ip'
    heartbeat_data = {
        'serial': serial,
        'ip': ip,
        'timestamp': strftime_time(time.localtime())
    }
    url = config['tempest_url']
    response = urequests.post(url + 'heartbeat', json=heartbeat_data)


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
        'now': strftime_time(time.localtime())
    }


def get_day(day):
    # another 5MS hack - today is actually yesterday
    day = day if day is not None else strftime_day(add_delta(time.localtime(), days=1))
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
    wlan = network.WLAN(network.STA_IF)
    return wlan.ifconfig()[2]


def cold_tick_loop():
    config = load_config()

    now = time.localtime()
    print('time now is {}, waiting for 5 minutes'.format(now))

    while True:
        now = time.localtime()
        if now[4] % 5 == 0:
            break
        time.sleep(1)
        
    now = time.localtime()            
    print('time now is {}, starting to tick'.format(now))
    while True:
        now = time.localtime()            
        print('time now is {}, doing a tick'.format(now))
        tick(config)
        now = time.localtime()            
        print('time now is {}, waiting for next 5 minutes'.format(now))
        time.sleep(300)

    

if __name__ == '__main__':
    cold_tick_loop()

