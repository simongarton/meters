import requests
import socket
import json

#
# agent.py
#
# the main agent for a simulated meter. this is installed on each meter,
# and will run ... wait.
#

# potential common method - but if duplicated, means no dependencies
def load_config():
    with open('config.json') as config_file:
        data = json.load(config_file)
    return data

# potential common method - but if duplicated, means no dependencies
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

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
    

if __name__ == '__main__':
    announce()
