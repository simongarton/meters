from flask import request, jsonify
from agent.app import app
from agent import agent
from datetime import datetime
import json

# routes.py
#
# the main routes code for the agent server. this should handle just the REST calls, 
# using the imported agent for functionality.
#

@app.route('/')
def get():
    data = agent.build_root_data()
    return jsonify(data)


@app.route('/config', methods=['GET'])
def get_config():
    return jsonify(agent.load_config())


@app.route('/config', methods=['POST'])
def post_config():
    data = request.json
    return jsonify(agent.save_config(data))

@app.route('/tick', methods=['POST'])
def post_tick():
    return jsonify(agent.tick())

@app.route('/day', methods=['GET'])
def get_day():
    day = request.args.get('day')
    day_data = agent.get_day(day)
    if day_data == None:
        return jsonify({}), 404
    return jsonify(day_data)

@app.route('/day', methods=['POST'])
def post_day():
    day = request.args.get('day')
    day_data = agent.upload_day(day)
    if day_data == None:
        return jsonify({}), 404
    return jsonify(day_data)

@app.route('/redial', methods=['POST'])
def post_redial():
    day = request.args.get('day')
    days_uploaded = agent.redial(day)
    return jsonify({'days_uploaded': days_uploaded})