from flask import request, jsonify
from tempest.app import app
from datetime import datetime
import json

# routes.py
#
# the main routes code for the tempest server
#

# potential common method - but if duplicated, means no dependencies
def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    return data

def save_config(data):
    with open('config.json', 'w') as config_file:
        json.dump(data, config_file)
    return data

def build_root_data():
    data = {
        'entity':'tempest',
        'timestamp': datetime.now()
    }
    return data

@app.route('/')
@app.route('/index')
def index():
    data = build_root_data()
    return jsonify(data)


@app.route('/announce', methods=['POST'])
def announce():
    data = request.json
    ip = data['ip']
    return jsonify('{"active":' + ip + '}')


@app.route('/config', methods=['GET'])
def get_config():
    return jsonify(load_config())


@app.route('/config', methods=['POST'])
def post_config():
    data = request.json
    return jsonify(save_config(data))

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    print(data)
    # save it; send to MDMS
    return jsonify(data)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    print(data)
    return jsonify(data)