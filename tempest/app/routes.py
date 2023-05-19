from flask import request, jsonify, render_template, make_response
from tempest.app import app
from tempest import tempest

# routes.py
#
# the main routes code for the tempest server. basically handles the routes and
# delegates everything else to tempest.
#

# CORS

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def jsonify_cors(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# GET

@app.route('/', methods=['OPTIONS'])
def get_index_options():
    return _build_cors_preflight_response()


@app.route('/heartbeats', methods=['OPTIONS'])
def get_heartbeats_options():
    return _build_cors_preflight_response()


@app.route('/meters', methods=['OPTIONS'])
def get_meters_options():
    return _build_cors_preflight_response()


@app.route('/meter', methods=['OPTIONS'])
def get_meter_options():
    return _build_cors_preflight_response()


@app.route('/')
def index():
    data = tempest.build_root_data()
    return jsonify_cors(data)


@app.route('/heartbeats', methods=['GET'])
def get_heartbeats():
    return jsonify_cors(tempest.get_heartbeats())


@app.route('/meters', methods=['GET'])
def get_meters():
    return jsonify_cors(tempest.get_meters())


@app.route('/meter', methods=['GET'])
def get_meter():
    serial = request.args.get('serial')
    day = request.args.get('day')
    datastream = request.args.get('datastream')
    if day == None:
        return jsonify_cors(tempest.get_meter(serial))
    if datastream == None:
        return jsonify_cors(tempest.get_meter_readings(serial, day))
    return jsonify_cors(tempest.get_meter_readings(serial, day, datastream))

# POST

@app.route('/heartbeat', methods=['POST'])
def post_heartbeat():
    return jsonify(tempest.post_heartbeat(request.json))


@app.route('/update', methods=['POST'])
def update():
    return jsonify(tempest.update(request.json))

# UI

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
