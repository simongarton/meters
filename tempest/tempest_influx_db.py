from tempest.token import get_token
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL = 'http://localhost:8086'
ORG = 'home'
BUCKET = 'meters'

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
                p = Point("consumption").tag("serial", serial).tag("datastream", datastream_name).field("reading", reading).time(dt_utc)
                write_api.write(bucket=BUCKET, org=ORG, record=p)


save_influx_data(serial, date, data)