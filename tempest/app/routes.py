from flask import request, jsonify, render_template
from tempest.app import app
from tempest import tempest

# routes.py
#
# the main routes code for the tempest server. basically handles the routes and 
# delegates everything else to tempest.
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
    return jsonify(tempest.get_meters())


@app.route('/meter', methods=['GET'])
def get_meter():
    serial = request.args.get('serial')
    day = request.args.get('day')
    if day == None:
        return jsonify(tempest.get_meter(serial))
    return jsonify(tempest.get_meter_readings(serial, day))


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


@app.route('/ui/meter', methods=['GET'])
def ui_meter():
    serial = request.args.get('serial')
    day = request.args.get('day')
    if day == None:
        meter_data = tempest.get_meter(serial)
        return render_template('meter.html', serial=serial, days=meter_data)
    readings = tempest.get_meter_readings(serial, day)
    return render_template('readings.html', serial=serial, day=day, readings=readings)
