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


def jsonify_cors(data):
    response = jsonify(data)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


# OPTIONS


@app.route("/", methods=["OPTIONS"])
def get_index_options():
    return _build_cors_preflight_response()


@app.route("/heartbeats", methods=["OPTIONS"])
def get_heartbeats_options():
    return _build_cors_preflight_response()


@app.route("/meters", methods=["OPTIONS"])
def get_meters_options():
    return _build_cors_preflight_response()


@app.route("/meter", methods=["OPTIONS"])
def get_meter_options():
    return _build_cors_preflight_response()


@app.route("/payload", methods=["OPTIONS"])
def get_payload_options():
    return _build_cors_preflight_response()


# GET


@app.route("/")
def index():
    data = tempest.build_root_data()
    return jsonify_cors(data)


@app.route("/heartbeats", methods=["GET"])
def get_heartbeats():
    return jsonify_cors(tempest.get_heartbeats())


@app.route("/meters", methods=["GET"])
def get_meters():
    return jsonify_cors(tempest.get_meters())


@app.route("/meters/<serial>", methods=["GET"])
def get_meter(serial):
    if serial == None:
        return jsonify({}), 400
    return jsonify_cors(tempest.get_meter(serial))


@app.route("/meters/<serial>/payloads", methods=["GET"])
def get_meter_payloads(serial):
    if serial == None:
        return jsonify({}), 400
    return jsonify_cors(tempest.get_meter_payloads(serial))


@app.route("/meters/<serial>/payloads/<payload_date>", methods=["GET"])
def get_meter_payload_datastreams(serial, payload_date):
    if serial == None:
        return jsonify({}), 400
    if payload_date == None:
        return jsonify({}), 400
    return jsonify_cors(tempest.get_meter_payload_datastreams(serial, payload_date))


@app.route("/meters/<serial>/payloads/<payload_date>/<datastream>", methods=["GET"])
def get_meter_payload_datastream(serial, payload_date, datastream):
    if serial == None:
        return jsonify({}), 400
    if payload_date == None:
        return jsonify({}), 400
    if datastream == None:
        return jsonify({}), 400
    return jsonify_cors(
        tempest.get_meter_payload_datastream(serial, payload_date, datastream)
    )


@app.route("/payload", methods=["GET"])
def get_payload():
    serial = request.args.get("serial")
    if serial == None:
        return jsonify({}), 400
    day = request.args.get("day")
    if day == None:
        return jsonify({}), 400
    return jsonify_cors(tempest.get_meter_payload(serial, day))


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify_cors(tempest.get_status())


# POST


@app.route("/heartbeat", methods=["POST"])
def post_heartbeat():
    return jsonify(tempest.post_heartbeat(request.json))


@app.route("/update", methods=["POST"])
def update():
    return jsonify(tempest.update(request.json))


@app.route("/upload", methods=["POST"])
def upload():
    return jsonify(tempest.upload(request.json))


# UI


@app.route("/ui/heartbeats", methods=["GET"])
def ui_heartbeats():
    heartbeat_data = tempest.get_heartbeats()
    heartbeats = []
    for k, e in heartbeat_data.items():
        heartbeats.append({"serial": k, "timestamp": e})
    return render_template("heartbeats.html", heartbeats=heartbeats)


@app.route("/ui/meters", methods=["GET"])
def ui_meters():
    meter_data = tempest.get_meters()
    meters = []
    for k, e in meter_data.items():
        meters.append(
            {
                "serial": k,
                "count": e["count"],
                "latest": e["latest"],
                "last_seen": e["last_seen"],
            }
        )
    return render_template("meters.html", meters=meters)


@app.route("/ui/meter", methods=["GET"])
def ui_meter():
    serial = request.args.get("serial")
    day = request.args.get("day")
    if day == None:
        meter_data = tempest.get_meter(serial)
        return render_template("meter.html", serial=serial, days=meter_data)
    readings = tempest.get_meter_readings(serial, day)
    return render_template("readings.html", serial=serial, day=day, readings=readings)
