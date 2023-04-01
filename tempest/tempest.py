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
    data = create_or_get_heartbeats()
    data[heartbeat['serial']] = datetime.strftime(datetime.now(), TIME_FORMAT)
    save_heartbeats(data)
    return data


def get_meters():
    return []


def get_meter(serial):
    return {}