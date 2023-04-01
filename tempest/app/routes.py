from flask import request, jsonify, render_template
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


@app.route('/update', methods=['POST'])
def update():
    return jsonify(tempest.update(request.json))


@app.route('/ui/heartbeats', methods=['GET'])
def ui_heartbeats():
    heartbeat_data = tempest.get_heartbeats()
    heartbeats = []
    for k,e in heartbeat_data.items():
        heartbeats.append(
            {
                'serial': k,
                'timestamp': e
             }
        )
    return render_template('heartbeats.html', heartbeats=heartbeats)

@app.route('/ui/meters', methods=['GET'])
def ui_meters():
    meter_data = tempest.get_meters()
    meters = []
    for k,e in meter_data.items():
        meters.append(
            {
                'serial': k,
                'count': e['count'],
                'latest': e['latest'],
                'last_seen': e['last_seen'],
             }
        )
    return render_template('meters.html', meters=meters)
