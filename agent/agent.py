import requests
import socket
import json
from datetime import datetime
from agent import meter

#
# agent.py
#
# the main agent for a simulated meter. this is installed on each meter,
# and will run ... wait.
#

def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    return data

def save_config(data):
    with open('config.json', 'w') as config_file:
        json.dump(data, config_file)
    return data

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def build_root_data():
    data = {
        'entity': 'agent',
        'timestamp': datetime.now(),
        'ip': get_ip()
    }
    return data

def announce():
    config = load_config()
    print(config)
    url = config['tempest_url']
    data = {
        'ip': get_ip()
    }
    response = requests.post(url + 'announce', json=data)
    print(response.status_code)
    print(response.json())
    
def tick():
    return meter.tick(load_config())
