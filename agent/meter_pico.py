#
# meter_pico.py
#
# the main logic for a meter - generating values and storing them. this is essentially the same
# as the main meter.py, but with various fixes for Picos running Micropython : datetime is gone,
# time.strptime() and time.strftime() don't work like datetime (and doesn't even work like time
# on real Python), urequests, no os.path.exists(), have to set time on startup using
# wifi secrets.

# Important
#
# Using time.localtime() and then writing out the times, I ended up with a UTC time (!) but not time zone aware.
# I have added strftime_time_utc() for when I write out to the file, to include a Z on the end - which I can then parse later
# I have also updated the logic for checking last_uploaded, last_updated as I also parse that manually (and the Z is ignored.)

# on the device via thonny, just before 10pm local
#
#>>> print(time.localtime())
#(2023, 5, 5, 21, 59, 23, 4, 125)
#>>> print(time.gmtime())
#(2023, 5, 5, 21, 59, 30, 4, 125)

# oh, but when I saw it start up
#
# time now is (2023, 5, 5, 10, 6, 58, 4, 125), waiting for whole minute
#
# and the next few were all GMT. but dropping back to a prompt gave me local times again.

# I have changed the format to have +10:00 rather than Z. Crossed fingers. 0.1.3. Delete out the existing files.

import time
import json
import random
import urequests
import network
import secrets
import ntptime
import os
from machine import Pin

# this is an empty class, with stub methods. if you look in the displays/folder, you can see other versions - with their appropriate
# drive files - of this file to support specific displays. displays from WaveShare.
import meter_pico_display


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'
APP_TITLE = "picoMeter"
VERSION = "0.1.3"
DATA_MODEL_VERSION = "1.0.0"

def round_time(dt=None, roundTo=60):
    if dt == None : dt = time.localtime()
    seconds = time.mktime(dt)
    remainder = seconds % roundTo
    return time.localtime(seconds - remainder)

def strftime_time(struct_time):
    # change this one depending. Also, local needs daylight savings
    # as the Pico is not daylight savings aware
    return strftime_time_local(struct_time)


def strftime_time_utc(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}T{:02.0f}:{:02.0f}:{:02.0f}Z".format(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], )


def strftime_time_local(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}T{:02.0f}:{:02.0f}:{:02.0f}+10:00".format(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], )


def strftime_time_simple(struct_time):
    return "{:02.0f}:{:02.0f}:{:02.0f}".format(struct_time[3], struct_time[4], struct_time[5], )


def strftime_day(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}".format(struct_time[0], struct_time[1], struct_time[2])


def strptime_time(struct_time_string):
    # assume I'm using '%Y-%m-%d %H:%M:%S' with or without the Z
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
    with open(filename, 'r') as payload:
        data = json.load(payload)
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
    
    reading = profile_value
    varied_reading = reading + (random.uniform(0, variability) * reading) - (2 * random.uniform(0, variability) * reading) 
    channel_reading = round(varied_reading * channel_factor, 3)
    
    missing_data = config['missing_data'] if 'missing_data' in config else 0
    excessive_data = config['excessive_data'] if 'excessive_data' in config else 0
    if random.uniform(0, 1) < missing_data:
        return None
    if random.uniform(0, 1) < excessive_data:
        channel_reading = random(0,1000)
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


def save_chart_reading(channel_name, reading):
    filename = 'charts/{}.csv'.format(channel_name)
    if not file_exists(filename):
        with open(filename, 'w') as output:
            output.write(str(reading))
        return
    readings = []
    with open(filename, 'r') as input:
        new_readings = input.readlines()
        for new_reading in new_readings:
            readings.append(float(new_reading))
    readings.append(reading)
    short_list = readings if len(readings) < 288 else readings[-288:]
    with open(filename, 'w') as output:
            for item in short_list:
                output.write('{}\n'.format(item))
    

def build_metadata_block(config):

    small_config = config.copy()
    small_config.pop('profile')
    return {
        'version': VERSION,
        'data_model_version': DATA_MODEL_VERSION,
        'config': small_config
    }


def create_or_update_readings(usable_time, serial, config, snapshot_block):
    updated_snapshot_block = snapshot_block.copy()
    reading_time =  map_timestamp_to_reading_day(usable_time)
    reading_day = strftime_day(reading_time)
    channel_data = config['channels'] if 'channels' in config else {"Total":1.0}
    datastream_block = build_datastream_block(channel_data)
    metadata_block = build_metadata_block(config)
    empty_day = {
        'serial': serial,
        'reading_day': reading_day,
        'snapshots': snapshot_block,
        'datastreams': datastream_block,
        'metadata': metadata_block
        }


    day = create_or_get_day(reading_day, empty_day)

    readings = []
    for channel_name, channel_factor in channel_data.items():
        reading = generate_reading(usable_time, config, channel_factor)
        if reading == None:
            continue
        save_chart_reading(channel_name, reading)
        readings.append((channel_name, reading))
        interval_key = strftime_time(usable_time)
        day['datastreams'][channel_name][interval_key] = reading
        updated_snapshot_block[channel_name] = updated_snapshot_block[channel_name] + reading
    save_updated_day(reading_day, day)
    return updated_snapshot_block, readings


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
    try:
        response = urequests.post(url + 'update', json=day_data)        
        return True
    except:
        print('failed to upload data for {} at {}'.format(reading_day, time.localtime()))
        return False


def upload_completed(config):
    metadata = create_or_load_metadata()   
    interval = config['interval_min'] * 60 
    usable_time = round_time(time.localtime(), interval)
    current_day = strftime_day(map_timestamp_to_reading_day(usable_time))
    current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
    if current_day_file == None or current_day != current_day_file:
        print('need to upload file as current_day is {} but working file is {}'.format(current_day, current_day_file))
        if upload_file(current_day_file, config):
            print("uploaded file worked, updating metadata to {}".format(current_day))
            metadata['last_uploaded'] = strftime_time(time.localtime())
            metadata['current_day_file'] = current_day
            save_metadata(metadata)
        else:
            print("uploaded file didn't work, updating metadata to {}".format(current_day))
            metadata['current_day_file'] = current_day
            save_metadata(metadata)
        return True
    print('no need to upload file as current_day is {} and working file is also {}'.format(current_day, current_day_file))
    return False


def tick_completed(config, force):
    metadata = create_or_load_metadata()    
    last_updated = metadata['last_updated']
    interval = config['interval_min'] * 60

    ready = force
    if last_updated == None:
        ready = True
    else:
        last_updated_time = time.localtime(strptime_time(last_updated))
        diff = seconds_between(time.localtime(), last_updated_time)    
        if diff > interval:
            ready = True

    if not ready:
        return False, []
    
    # there is a bit of a gotcha here. I need to record the 5 minute interval (or 30 etc) for this
    # which can only happen every 5 minutes. but I may have gone past this time.
    # for now, I'm going to have a USABLE time which is the 5 minute (or 30 minute) interval before this one
    # ... which I think I shouldn't get a duplicate for (and is OK anyway, as it's keyed)

    usable_time = round_time(time.localtime(), interval)
    print('converted {} to usable time {} for interval {}'.format(time.localtime(), usable_time, interval))

    snapshot_block = create_or_get_snapshot_block(config, metadata)

    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    updated_snapshot_block, readings = create_or_update_readings(usable_time, serial, config, snapshot_block)

    metadata['snapshots'] = updated_snapshot_block
    metadata['last_updated'] = strftime_time(usable_time)

    save_metadata(metadata)
    return True, readings


def connect():
    print('connecting to {}'.format(secrets.SSID))
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.SSID, secrets.PASSWORD)
    print('connected to wifi : {}'.format(wlan.isconnected()))


def heartbeat(config):
    if demo_mode(config):
        return
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


def tick(config, force):
    status = ''
    # run a tick (if ready) to store some more 5min data
    outcome, readings = tick_completed(config, force)
    if outcome == False:
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

    try:
        heartbeat(config)
    except Exception as e:
        print('no heartbeat : {}'.format(str(e)))

    return {
        'status': status,
        'now': strftime_time(time.localtime()),
        'readings': readings,
        'updated': outcome
    }


def get_day(day):
    # another 5MS hack - today is actually yesterday
    day = day if day is not None else strftime_day(add_delta(time.localtime(), days=1))
    return get_day_data(day)
    

def upload_day(day, config):
    try:
        return upload_file(day, config)
    except:
        print('no upload possible')


def redial(from_day, config):
    # TBC - count the number of payloads I actually redial
    return 0


def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    try:
        data['ip'] = get_ip()
    except:
        data['ip'] = '0.0.0.0'
    return data


def get_ip():
    wlan = network.WLAN(network.STA_IF)
    return wlan.ifconfig()[2]


def wait_until_time_set(config):
    # have at least 2 flash sequence to show setting time
    config = load_config()
    led = find_onboard_led(config)

    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
    count = 0
    while True:
        try:
            led.on()
            time.sleep(0.5)
            led.off()
            time.sleep(0.5)
            ntptime.settime()
            return True
        except:    
            print('could not set time')
        count = count + 1
        if count > 10:
            return False


def demo_mode(config):
    if not 'demo' in config:
        return False
    return config['demo']


def find_onboard_led(config):
    # for a regular Pico
    led = Pin(25, Pin.OUT)
    if not 'model' in config:
        return led
    if config['model'] == 'pico-w':
        # for a Pico W
        led = machine.Pin("LED", machine.Pin.OUT)
    return led


def generate_readings(config):
    number_points = 288 # TODO fixed for 5 minutes, chart willl look bad with 30
    seconds = time.time() - (24 * 60 * 60)
    usable_time = time.localtime(seconds)
    channel_data = config['channels'] if 'channels' in config else {"Total":1.0}
    for channel_name, channel_factor in channel_data.items():
        filename = 'charts/{}.csv'.format(channel_name)
        if file_exists(filename):
            continue

        readings = []
        for interval in range(number_points):
            reading = generate_reading(usable_time, config, channel_factor)
            if reading != None:
                readings.append(reading)
            seconds = seconds + (5 * 60)
            usable_time = time.localtime(seconds)

        short_list = readings if len(readings) < 288 else readings[-288:]
        with open(filename, 'w') as output:
            for item in short_list:
                output.write('{}\n'.format(item))


def update_chart_readings(chart_readings, display_readings):
    for (channel_name, value) in display_readings:
        if not channel_name in chart_readings:
            chart_readings[channel_name] = []
        chart_readings[channel_name].append(value)
        if len(chart_readings[channel_name]) > 288:
            chart_readings[channel_name].pop(0)
    return chart_readings


def cold_tick_loop():
    config = load_config()
    led = find_onboard_led(config)
    interval = config['interval_min']

    meter_pico_display.display_single_message("hello, I'm {}".format(config['serial']))

    print('before wifi')
    print('time.localtime() now is {}',time.localtime()) 
    print('time.gmtime() now is {}',time.gmtime()) 

    if not demo_mode(config):
        connect()
        time_set = wait_until_time_set(config)

    print('after wifi')
    print('time.localtime() now is {}',time.localtime()) 
    print('time.gmtime() now is {}',time.gmtime()) 

    if demo_mode(config):
        generate_readings(config)

    now = time.localtime()
    print('time now is {}, waiting for whole minute'.format(now))

    while True:
        now = time.localtime()
        if now[5] % 60 == 0:
            break
        meter_pico_display.display_single_message("waiting ({})".format(now[5]))
        led.on() # brief flash every second to show waiting
        time.sleep(0.1)
        led.off()
        time.sleep(0.9)
        # TODO 
        break
        
    meter_pico_display.display_single_message("starting ...")
    print('time now is {}, starting to tick'.format(now))
    display_readings = []
    iteration = 0
    while True:
        elapsed = time.time()    
        now = time.localtime()            
        print('time now is {}, doing a tick'.format(now))
        led.on() # 1 second pulse to show uploading
        tick_details = tick(config, len(display_readings) == 0)
        time.sleep(1)
        led.off()
        time.sleep(1)
        now = time.localtime()            
        print('time now is {}, waiting for next minute'.format(now))
        if tick_details['updated']:
            display_readings = tick_details['readings']
        while True:
            now = time.localtime()
            iteration = display_something(iteration, now, display_readings, interval)
            led.on() # brief flash every 5 seconds to show alive
            time.sleep(0.1)
            led.off()
            time.sleep(4.9)
            now = time.localtime()
            if now[5] % 60 == 0: # on the minute
                break
            if time.time() - elapsed >= 60: # safety
                break

def display_something(iteration, now, display_readings, interval):           
    if iteration % 4 == 0:
        meter_pico_display.display_last_values(strftime_time_simple(now), display_readings, interval)
    if iteration % 4 == 1:
        meter_pico_display.display_line_chart(strftime_time_simple(now), display_readings, interval)
    if iteration % 4 == 2:
        meter_pico_display.display_bar_chart(strftime_time_simple(now), display_readings, interval)
    if iteration % 4 == 3:
        meter_pico_display.display_total_chart(strftime_time_simple(now), display_readings, interval)
    iteration = iteration + 1
    return iteration
    
def force_upload():
    config = load_config()
    if demo_mode(config):
        return
    connect()
    status = ''

    if upload_completed(config) == False:
        status = status + 'not ready to upload. '
    else:
        status = status + 'upload completed.'  
    print(status)    


def blink_five_times_to_start():
    config = load_config()
    led = find_onboard_led(config)

    for i in range(5):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
    time.sleep(1)


if __name__ == '__main__':
    try:
        os.mkdir('data')
    except:
        pass

    try:
        os.mkdir('charts')
    except:
        pass

    blink_five_times_to_start()
    meter_pico_display.splash_screen('{} {} ({})'.format(APP_TITLE, VERSION, DATA_MODEL_VERSION))
    #force_upload()
    cold_tick_loop()
