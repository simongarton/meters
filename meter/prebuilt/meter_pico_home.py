#
# meter_pico.py
#
# the main logic for a meter - generating values and storing them. this is essentially the same
# as the main meter.py, but with various fixes for Picos running Micropython : datetime is gone,
# time.strptime() and time.strftime() don't work like datetime (and doesn't even work like time
# on real Python), urequests, no os.path.exists(), have to set time on startup using
# wifi secrets.

# Time is a pain
# time.localtime() and time.gmtime() return the same value on MicroPython/Pico
# ntptime().settime() sets me to UTC.
#
# There is a call I could make : "http://worldtimeapi.org/api/timezone/Pacific/Auckland"
#
# Howeever, I think I'm just going to apply an offset. And one day I need to do daylight savings.

# version history
#
# 0.3.2 : 2023-05-25 WDT off again
# 0.3.1 : 2023-05-25 WDT tweaked; going to cloud HeadEnd
# 0.3.0 : 2023-05-19 WDT back in; consolidating
# 0.2.4 : 2023-05-14 WDT again just for pico-001
# 0.2.3 : 2023-05-13 removed machine ID, not UTF-8
# 0.2.2 : 2023-05-13 remove watchdog - not sure now if it needed to, but early creation makes working with it hard
# 0.2.1 : 2023-05-12 add watchdog, machine ID
# 0.2.0 : 2023-05-05 redone time with offsets for local

import time
import json
import random
import urequests
import network
import secrets
import ntptime
import os
from machine import Pin, WDT

# this is an empty class, with stub methods. if you look in the displays/folder, you can see other versions - with their appropriate
# drive files - of this file to support specific displays. displays from WaveShare.
import meter_pico_display


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'
APP_TITLE = "picoMeter"
VERSION = "0.3.2"
DATA_MODEL_VERSION = "1.0.0"
OFFSET_HOURS = 12
OFFSET = '+12:00'

YEAR = 2022

def round_time(dt=None, roundTo=60):
    if dt == None : dt = time.localtime()
    seconds = time.mktime(dt)
    remainder = seconds % roundTo
    return time.localtime(seconds - remainder)


def convert_time_to_local(struct_time):
    # cross reference add_delta()
    seconds = time.mktime(struct_time)
    seconds = seconds + OFFSET_HOURS * 60 * 60
    return time.localtime(seconds)


def localtime():
    return convert_time_to_local(time.localtime())


def strftime_time(struct_time):
    # change this one depending on what output you want.
    # Remember the Pico is not daylight savings aware
    return strftime_time_local(struct_time)


def strftime_time_utc(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}T{:02.0f}:{:02.0f}:{:02.0f}Z".format(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], )


def strftime_time_local(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}T{:02.0f}:{:02.0f}:{:02.0f}{}".format(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], OFFSET)


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


# add this

def get_reading_from_file(month, day, hour, min, divisor):
    date = '{:04d}-{:02d}-{:02d}'.format(YEAR, month, day)
    month = '{:04d}-{:02d}'.format(YEAR, month)
    time = '{:02d}:{:02d}'.format(hour, min)
    filename = 'months/{}.csv'.format(month)
    with open(filename, 'r') as csvfile:
        while True:
            row = csvfile.readline()
            if not row:
                break
            row_data = row.split(',')
            if row_data[0] == date:
                if row_data[1] == time:
                    return round(1000 * float(row_data[2]) / divisor) / 1000.0

# and change this method

def generate_reading(usable_time, config, channel_name, channel_factor):
    month = usable_time[1]
    day = usable_time[2]
    hour = usable_time[3]
    min = usable_time[4]
    min30 = (min // 30) * 30
    return get_reading_from_file(month, day, hour, min30, 6)


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
        'interval': config['interval_min'],
        'snapshots': snapshot_block,
        'datastreams': datastream_block,
        'metadata': metadata_block
        }


    day = create_or_get_day(reading_day, empty_day)

    readings = []
    for channel_name, channel_factor in channel_data.items():
        reading = generate_reading(usable_time, config, channel_name, channel_factor)
        if reading == None:
            continue
        if demo_mode(config):
            save_chart_reading(channel_name, reading)
        readings.append((channel_name, reading))
        interval_key = strftime_time(usable_time)
        day['datastreams'][channel_name][interval_key] = reading
        print('{} @ {} -> {}'.format(channel_name, interval_key, reading))
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
        print('no data to load for {} at {}'.format(reading_day, localtime()))
        return False
    # print('got data to load for {} at {}'.format(reading_day, localtime()))

    url = config['tempest_url']
    api_key = config['tempest_api_key']
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    try:
        response = urequests.post(url + '/updates', headers=headers, json=day_data)
        print(url + '/updates : {}'.format(response.status_code))
        return True
    except:
        print('failed to upload data for {} at {}'.format(reading_day, localtime()))
        return False


def upload_completed(config):
    metadata = create_or_load_metadata()
    interval = config['interval_min'] * 60
    usable_time = round_time(localtime(), interval)
    current_day = strftime_day(map_timestamp_to_reading_day(usable_time))
    current_day_file = metadata['current_day_file'] if 'current_day_file' in metadata else None
    if current_day_file == None or current_day != current_day_file:
        print('need to upload file as current_day is {} but working file is {}'.format(current_day, current_day_file))
        if upload_file(current_day_file, config):
            print("uploaded file worked, updating metadata to {}".format(current_day))
            metadata['last_uploaded'] = strftime_time(localtime())
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
        diff = seconds_between(localtime(), last_updated_time)
        if diff > interval:
            ready = True

    if not ready:
        return False, []

    # there is a bit of a gotcha here. I need to record the 5 minute interval (or 30 etc) for this
    # which can only happen every 5 minutes. but I may have gone past this time.
    # for now, I'm going to have a USABLE time which is the 5 minute (or 30 minute) interval before this one
    # ... which I think I shouldn't get a duplicate for (and is OK anyway, as it's keyed)

    usable_time = round_time(localtime(), interval)
    print('converted {} to usable time {} for interval {}'.format(localtime(), usable_time, interval))

    snapshot_block = create_or_get_snapshot_block(config, metadata)

    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    updated_snapshot_block, readings = create_or_update_readings(usable_time, serial, config, snapshot_block)

    metadata['snapshots'] = updated_snapshot_block
    metadata['last_updated'] = strftime_time(usable_time)

    save_metadata(metadata)
    return True, readings


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True
    while True:
        print('connecting to {}'.format(secrets.SSID))
        wlan.connect(secrets.SSID, secrets.PASSWORD)
        print('connected to wifi : {}'.format(wlan.isconnected()))
        if wlan.isconnected():
            return True
        time.sleep(5)


def heartbeat(config):
    if demo_mode(config):
        return
    connect()
    serial = config['serial'] if 'serial' in config else 'no-serial-number'
    ip = config['ip'] if 'ip' in config else 'no-ip'
    heartbeat_data = {
        'serial': serial,
        'ip': ip,
        'timestamp': strftime_time(localtime())
    }

    url = config['tempest_url']
    api_key = config['tempest_api_key']
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = urequests.post(url + '/heartbeats', headers=headers, json=heartbeat_data)
        print(url + '/heartbeats : {}'.format(response.status_code))
        return True
    except:
        print('failed to heartbeat  at {}'.format(localtime()))
        return False


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
        'now': strftime_time(localtime()),
        'readings': readings,
        'updated': outcome
    }


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
            print('calling ntptime() ...')
            ntptime.settime()
            now = time.localtime()
            print("used ntptime() to set time to UTC, time.localttime() is : {}".format(now))
            converted = localtime()
            print("my localtime is now : {}".format(converted))
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
            reading = generate_reading(usable_time, config, channel_name, channel_factor)
            if reading != None:
                readings.append(reading)
            seconds = seconds + (5 * 60)
            usable_time = time.localtime(seconds)

        short_list = readings if len(readings) < 288 else readings[-288:]
        with open(filename, 'w') as output:
            for item in short_list:
                output.write('{}\n'.format(item))


def write_startup_message(message):
    with open('startup.log', 'a') as output:
        output.write('{} : {}\n'.format(localtime(), message))


def cold_tick_loop():
    config = load_config()
    led = find_onboard_led(config)
    interval = config['interval_min']

    meter_pico_display.display_single_message("hello, I'm {}".format(config['serial']))

    if not demo_mode(config):
        connect()
        time_set = wait_until_time_set(config)
        write_startup_message('real startup, time set')
    else:
        generate_readings(config)
        write_startup_message('demo startup, readings generated')

    now = localtime()
    converted = convert_time_to_local(now)
    print('time now is {}, converted time {}, waiting for whole minute'.format(now, converted))

    while True:
        now = localtime()
        if now[5] % 60 == 0:
            break
        meter_pico_display.display_single_message("waiting ({})".format(now[5]))
        led.on() # brief flash every second to show waiting
        time.sleep(0.1)
        led.off()
        time.sleep(0.9)

    meter_pico_display.display_single_message("starting ...")
    print('time now is {}, starting to tick'.format(now))
    display_readings = []
    iteration = 0

    # wdt = WDT(timeout=8000) # milliseconds
    while True:
        elapsed = time.time()
        now = localtime()
        print('time now is {}, doing a tick'.format(now))
        led.on() # 1 second pulse to show uploading
        tick_details = tick(config, len(display_readings) == 0)
        time.sleep(1)
        led.off()
        time.sleep(1)
        now = localtime()
        print('time now is {}, waiting for next minute'.format(now))
        if tick_details['updated']:
            display_readings = tick_details['readings']
        # wdt.feed()
        while True:
            now = localtime()
            iteration = display_something(iteration, now, display_readings, interval)
            led.on() # brief flash every 5 seconds to show alive
            time.sleep(0.1)
            led.off()
            time.sleep(4.9)
            now = localtime()
            if now[5] % 60 == 0: # on the minute
                break
            if time.time() - elapsed >= 60: # safety
                break
            # feed the watchdog
            # wdt.feed()
            # reboot after 24 hours
            if iteration >= 17280:
                write_startup_message('rebooting after 24 hours')
                machine.reset()


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
    cold_tick_loop()
