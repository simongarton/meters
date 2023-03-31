from flask import render_template, request, jsonify
from app import app
import json

# potential common method
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