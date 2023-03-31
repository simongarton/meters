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