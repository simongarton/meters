from flask import request, jsonify
from tempest.app import app
from tempest import tempest
from datetime import datetime
import json

# routes.py
#
# the main routes code for the tempest server
#

@app.route('/')
def index():
    data = tempest.build_root_data()
    return jsonify(data)

@app.route('/heartbeat', methods=['POST'])
def post_heartbeat():
    return jsonify(tempest.post_heartbeat(request.json))


@app.route('/heartbeats', methods=['GET'])
def get_heartbeats():
    return jsonify(tempest.get_heartbeats())


@app.route('/meters', methods=['GET'])
def get_meters():
    serial = request.args.get('serial')
    if serial == None:
        return jsonify(tempest.get_meters())
    return jsonify(tempest.get_meter(serial))