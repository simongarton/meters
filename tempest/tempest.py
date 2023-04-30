from datetime import datetime
import socket
import os
import json
import requests
import secrets

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
        json.dump(data, file, indent=4)
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
        json.dump(data, file, indent=4)
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



def save_data(serial, date, data):
    dirname = 'data/{}'.format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = 'data/{}/{}.json'.format(serial, date)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    file_count = len(os.listdir(dirname))
    meter_data = create_or_get_meters()
    entry = {
        'count':file_count,
        'latest': date,
        'last_seen': datetime.strftime(datetime.now(), TIME_FORMAT)
    }
    meter_data[serial] = entry
    save_meters(meter_data)

    return data


def convert_to_pipeline_format(data):
    # this is the ProcessingPayload format from the pipeline.
    meter = {}
    meter['serialNumber'] = data['serial']

    unit_of_work = {}
    unit_of_work['serialNumber'] = data['serial']
    # TODO I need to do this properly
    unit_of_work['payloadDate'] = '{}T00:00:00Z'.format(data['reading_day'])

    datastreams = []
    for name, reading_data in data['datastreams']:
        datastream = {}
        datastream['name'] = name
        datastream['interval'] = 5 # TODO this should come from metadata but is missing.
        
        readings = []
        for timestamp, value in reading_data.items():
            readings.append({
                'timestamp': timestamp,
                'value': value
            })
        datastream['readings'] = readings
        datastreams.append(datastream)

    unit_of_work['dataStreams'] = datastreams
    converted_data = {
        'meter': meter,
        'unitOfWork': unit_of_work
    }

    return converted_data


def get_headers():
    return {
        'x-api-key': secrets.API_KEY,
        'Content-Type': 'application/json' 
    }
    

def upload_to_pipeline(serial, date, data):
    converted_data = convert_to_pipeline_format(data)
    print(converted_data)
    url = secrets.URL
    headers = get_headers()
    response = requests.post(url + 'ingestions', json=converted_data, headers=headers)
    print(response.status_code)
    print(response.json())


def update(data):
    serial = data['serial']
    date = data['reading_day']
    save_data(serial, date, data)
    upload_to_pipeline(serial, date, data)
