from datetime import datetime, timezone
import socket
import os
import json
import pytz


# run the SCP copy first : scp.sh
# that will put files in ./data

from influxdb_token import get_token
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

INFLUX_URL = 'http://localhost:8086'
ORG = 'home'
BUCKET = 'meters'
PATH = './data'

def save_influx_data(serial, date, data):
    token = get_token()
    client = InfluxDBClient(url=INFLUX_URL, token=token, org=ORG)
    with client.write_api(write_options=SYNCHRONOUS) as write_api:
        for datastream_name, datastream_values in data['datastreams'].items():
            for timestamp, reading in datastream_values.items():
                # this seems overly complex - but it works
                # 2023-04-01 20:35:00+13:00 -> 2023-04-01 07:35:00+00:00 -> 2023-04-01 07:35:00+00:00
                # maybe I can dt.replace(tzinfo=timezone.utc) ? Does that add the offset ?
                real_time = datetime.strptime(timestamp, TIME_FORMAT)
                dt_pacific = real_time.astimezone(pytz.timezone('Pacific/Auckland'))
                dt_utc = dt_pacific.astimezone(pytz.UTC)
                p = Point("consumption").tag("serial", serial).tag("datastream", datastream_name).field("reading", reading * 1.0).time(dt_utc)
                write_api.write(bucket=BUCKET, org=ORG, record=p)



# I have measurements from the picos at "2023-04-06T17:40:00": 4.138, which is correct for UTC, but doesn't have time zone info
# associateed with it.
# that is weirdly being forced into a local time same digits.
# kili has "2023-04-07T05:45:00" which is the correct local time, no time zone associated with it.
# I use time.localtime() in the picos
# 2. have a look at time.gmtime() on the pico, what does it do ?
# 1. since I write out my own strftime on the pico, can I add a Z to get it to UTC ? how does strptime() on the Pi 3 then handle it
#  ... ignores the Z. No, it needs %Z
# 
# >>> TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
# >>> print(datetime.strptime('2023-04-06T17:40:00Z', TIME_FORMAT))
# 2023-04-06 17:40:00+00:00
# >>> 


def load_data():
    for r, d, f in os.walk(PATH):
        for file in f:
            if 'meters' in file:
                continue
            if 'heartbeats' in file:
                continue
            if '.json' in file:
                print(os.path.join(r, file))
                with open(os.path.join(r, file), 'r') as payload:
                    data = json.load(payload)
                    serial = data['serial']
                    save_influx_data(serial, None, data)
    


if __name__ == '__main__':
    load_data()