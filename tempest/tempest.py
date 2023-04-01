from datetime import datetime
import socket
import os
import json

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAY_FORMAT = '%Y-%m-%d'


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


def save_data(serial, date, data):
    dirname = 'data/{}'.format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = 'data/{}/{}.json'.format(serial, date)
    with open(filename, 'w') as file:
        json.dump(data, file)
    file_count = len(os.listdir(dirname))
    data = create_or_get_meters()
    entry = {
        'count':file_count,
        'latest': date,
        'last_seen': datetime.strftime(datetime.now(), TIME_FORMAT)
    }
    data[serial] = entry
    save_meters(data)

    return data


def update(data):
    serial = data['serial']
    date = data['reading_day']
    save_data(serial, date, data)
