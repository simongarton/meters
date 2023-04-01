# Meters

Simon Garton
simon.garton@gmail.com
simongarton.com

March 2023

## About

This project explores setting up Raspberry Pis to simulate electricity meters, generating realistic daily
profiles of electricity consumption, that can be pushed to an MDMS.

## Getting Started

### Raspberry Pi

You'll need to do some stuff to get it set up. 

- Create a directory called agent in home : /home/pi/agent
- Copy the files : __init__.py, agent.py, config.json, meter.py, meter.sh, run.sh
- Copy the app directory : __init__.py and routes.py

#### run.sh

```
cd /home/pi/agent
sudo flask run --host 0.0.0.0
```

#### meter.sh

```
cd /home/pi/agent
sudo python3 /home/pi/agent/meter.py 
```

### Tempest

This acts as the head end, plus the asset management system.

- New 'meters' coming on line will announce their existence to Tempest
- Tempest can update their config, and possibly their business logic

### Meter

Several things run on the Pi.

- `agent.py` is invoked on startup. It runs a Flask web server to accept REST calls; it also makes a timed
announcement call to Tempest to say it is on line. I am considering a heartbeat as well.
- a CRON job runs every 5 minutes, on the 5 minute, to invoke `meter.py`
- `meter.py` is invoked every 5 minutes and makes decisions, based on it's config, which is stored in `config.json`



## Meter API


## Config