from datetime import datetime, timezone
import socket
import os
import json
from tempest.token import get_token
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pytz

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'
INFLUX_URL = 'http://localhost:8086'
ORG = 'home'
BUCKET = 'meters'

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def build_root_data():
    data = {
        'entity': 'tempest',
        'ip': get_ip(),
        'timestamp': datetime.now()
    }
    return data


def create_or_get_meters():
    if not os.path.exists('data'):
        os.mkdir('data')
    filename = 'data/meters.json'
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
        return data
    else:
        return {}


def save_meters(data):
    filename = 'data/meters.json'
    with open(filename, 'w') as file:
        json.dump(data, file)
    return data


def create_or_get_heartbeats():
    if not os.path.exists('data'):
        os.mkdir('data')
    filename = 'data/heartbeats.json'
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
        return data
    else:
        return {}


def save_heartbeats(data):
    filename = 'data/heartbeats.json'
    with open(filename, 'w') as file:
        json.dump(data, file)
    return data
    

def get_heartbeats():
    data = create_or_get_heartbeats()
    return data


def post_heartbeat(heartbeat):
    print(heartbeat)
    data = create_or_get_heartbeats()
    data[heartbeat['serial']] = datetime.strftime(datetime.now(), TIME_FORMAT)
    save_heartbeats(data)
    return data


def get_meters():
    return create_or_get_meters()


def get_meter(serial):
    dirname = 'data/{}'.format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    days = []
    for file in os.listdir(dirname):
        days.append(file.replace('.json', ''))
    days.sort(reverse=True)
    return days


def get_meter_readings(serial, day):
    dirname = 'data/{}'.format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = 'data/{}/{}.json'.format(serial, day)
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as file:
        data = json.load(file)
    readings = []
    skip_keys = ['serial', 'reading_day']
    for k,e in data.items():
        if k in skip_keys:
            continue
        readings.append({
            'timestamp': k,
            'value': e
        })
    return readings

def save_influx_data(serial, date, data):
    token = get_token()
    client = InfluxDBClient(url=INFLUX_URL, token=token, org=ORG)
    with client.write_api(write_options=SYNCHRONOUS) as write_api:
        skip_keys = ['serial', 'reading_day']
        for k,e in data.items():
            if k in skip_keys:
                continue
            # this seems overly complex - but it works
            # 2023-04-01 20:35:00+13:00 -> 2023-04-01 07:35:00+00:00 -> 2023-04-01 07:35:00+00:00
            real_time = datetime.strptime(k, TIME_FORMAT)
            dt_pacific = real_time.astimezone(pytz.timezone('Pacific/Auckland'))
            dt_utc = dt_pacific.astimezone(pytz.UTC)
            time = datetime(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second, 0, tzinfo=timezone.utc)
            # print('{} -> {} -> {}'.format(dt_pacific, dt_utc, time))
            p = Point("consumption").tag("serial", serial).field("reading", e).time(time)
            write_api.write(bucket=BUCKET, org=ORG, record=p)


def save_data(serial, date, data):
    dirname = 'data/{}'.format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = 'data/{}/{}.json'.format(serial, date)
    with open(filename, 'w') as file:
        json.dump(data, file)
    file_count = len(os.listdir(dirname))
    meter_data = create_or_get_meters()
    entry = {
        'count':file_count,
        'latest': date,
        'last_seen': datetime.strftime(datetime.now(), TIME_FORMAT)
    }
    meter_data[serial] = entry
    save_meters(meter_data)

    save_influx_data(serial, date, data)

    return data


def update(data):
    serial = data['serial']
    date = data['reading_day']
    save_data(serial, date, data)
