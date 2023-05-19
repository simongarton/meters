from datetime import datetime
import socket
import os
import json
import requests

# version history
#
# 0.3.0 : 2023-05-19 new endpoints
# 0.2.0 : 2023-05-05 secrets as json, two endpoints

with open("secrets.json", "r") as config_file:
    secrets = json.load(config_file)

PIPELINE_URL = secrets["url"]
API_KEY = secrets["api_key"]

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"  # not used
DAY_FORMAT = "%Y-%m-%d"
VERSION = "0.2.0"

CONVERT_TO_PIPELINE = False

# worry about this growing
ENABLE_SERVER_LOG = False


def log(message):
    if not ENABLE_SERVER_LOG:
        print(message)
        return
    filename = "tempest_server.log"
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode) as output:
        output.write("{} : {}\n".format(datetime.now(), message))


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def now_to_second():
    return datetime.now().replace(second=0, microsecond=0)


def build_root_data():
    data = {
        "entity": "tempest",
        "ip": get_ip(),
        "now": now_to_second().isoformat(),
        "timestamp": round(datetime.now().timestamp()),
    }
    return data


def create_or_get_meters():
    if not os.path.exists("data"):
        os.mkdir("data")
    filename = "data/meters.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            data = json.load(file)
        return data
    else:
        return {}


def save_meter_data(data):
    filename = "data/meters.json"
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    return data


def convert_heartbeats_to_list(data):
    list = []
    for serial_number, last_seen in data.items():
        last_communicated = datetime.fromisoformat(last_seen)
        elapsed_seconds = round(
            datetime.now().timestamp() - last_communicated.timestamp()
        )

        list.append({
            "serialNumber": serial_number,
            "timeLastCommunicated": last_seen,
            "elapsedSeconds": elapsed_seconds
            })
    list.sort(key= lambda x:x['elapsedSeconds'])
    return list


def create_or_get_heartbeats():
    if not os.path.exists("data"):
        os.mkdir("data")
    filename = "data/heartbeats.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            data = json.load(file)
        return data
    else:
        return {}


def save_heartbeats(data):
    filename = "data/heartbeats.json"
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    return data


def get_heartbeats():
    data = create_or_get_heartbeats()
    return convert_heartbeats_to_list(data)


def post_heartbeat(heartbeat):
    log("heartbeat {}".format(heartbeat))
    print(heartbeat)
    data = create_or_get_heartbeats()
    data[heartbeat["serial"]] = now_to_second().isoformat()
    save_heartbeats(data)
    return data


def convert_meters_to_list(data):
    list = []
    for serial_number, meter_data in data.items():
        # temporary, for old data
        time_key = (
            "timeLastCommunicated"
            if "timeLastCommunicated" in meter_data
            else "last_seen"
        )
        count_key = (
            "countOfFilesAvailable"
            if "countOfFilesAvailable" in meter_data
            else "count"
        )
        latest_key = "latestFile" if "latestFile" in meter_data else "latest"
        last_communicated = datetime.fromisoformat(meter_data[time_key])
        elapsed_seconds = round(
            datetime.now().timestamp() - last_communicated.timestamp()
        )
        list.append(
            {
                "serialNumber": serial_number,
                "timeLastCommunicated": meter_data[time_key],
                "elapsedSeconds": elapsed_seconds,
                "countOfFilesAvailable": meter_data[count_key],
                "latestFile": meter_data[latest_key],
            }
        )

    list.sort(key= lambda x:x['elapsedSeconds'])
    return list


def get_meters():
    data = create_or_get_meters()
    return convert_meters_to_list(data)


def get_meter_payload_datastream(serial_number, payload_date, datastream_name):
    dirname = "data/{}".format(serial_number)
    if not os.path.exists(dirname):
        return {}
    filename = "data/{}/{}.json".format(serial_number, payload_date)
    with open(filename, "r") as input:
        payload = json.load(input)
    datastream_data =  payload["datastreams"][datastream_name]
    data = []
    for timestamp, value in datastream_data.items():
        data.append({
            'timestamp':timestamp,
            'value':value
        })
    data.sort(key= lambda x:x['timestamp'])
    return data


def get_meter_payload_datastreams(serial_number, payload_date):
    dirname = "data/{}".format(serial_number)
    if not os.path.exists(dirname):
        return {}
    filename = "data/{}/{}.json".format(serial_number, payload_date)
    with open(filename, "r") as input:
        payload = json.load(input)
    payload_datastreams = []
    for datastream_name, datastream_data in payload["datastreams"].items():
        total_value = 0
        earliest = None
        latest = None
        count = 0
        for timestamp, value in datastream_data.items():
            count = count + 1
            total_value = total_value + value
            reading_time = datetime.fromisoformat(timestamp)
            if not earliest or (earliest - reading_time).seconds < 0:
                earliest = reading_time
            if not latest or (latest - reading_time).seconds > 0:
                latest = reading_time
        payload_datastreams.append(
            {
                "name": datastream_name,
                "measurements": count,
                "totalValue": round(1000 * total_value) / 1000,
                "earliest": earliest.isoformat(),
                "latest": latest.isoformat(),
            }
        )
    return payload_datastreams


def get_meter_payload(serial_number, payload_date):
    dirname = "data/{}".format(serial_number)
    if not os.path.exists(dirname):
        return {}
    filename = "data/{}/{}.json".format(serial_number, payload_date)
    with open(filename, "r") as input:
        payload = json.load(input)
    return payload


def get_meter_payloads(serial_number):
    dirname = "data/{}".format(serial_number)
    if not os.path.exists(dirname):
        return []
    meter_files = []
    for payload_date in os.listdir(dirname):
        filename = "data/{}/{}".format(serial_number, payload_date)
        with open(filename, "r") as input:
            payload = json.load(input)
        snapshots = len(payload["snapshots"])
        datastreams = len(payload["datastreams"])
        interval = payload["interval"]
        metadata = payload["metadata"]
        meter_version = metadata["version"] if "version" in metadata else "?"
        data_model_version = (
            metadata["data_model_version"] if "data_model_version" in metadata else "?"
        )
        meter_files.append(
            {
                "filename": filename,
                "serialNumber": serial_number,
                "payloadDate": payload_date.replace('.json',''),
                "meterVersion": meter_version,
                "dataModelVersion": data_model_version,
                "interval": interval,
                "snapshots": snapshots,
                "datastreams": datastreams,
            }
        )
    return meter_files


def get_meter(serial):
    dirname = "data/{}".format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    days = []
    for file in os.listdir(dirname):
        days.append(file.replace(".json", ""))
    days.sort(reverse=True)
    return {
        'serialNumber': serial,
        'payloads': len(days),
    }


def get_meter_readings(serial, day):
    dirname = "data/{}".format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    filename = "data/{}/{}.json".format(serial, day)
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as file:
        data = json.load(file)
    readings = []
    skip_keys = ["serial", "reading_day"]
    for k, e in data.items():
        if k in skip_keys:
            continue
        readings.append({"timestamp": k, "value": e})
    return readings


def save_all_data(serial, date, data):
    dirname = "data/{}".format(serial)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    filename = "data/{}/{}.json".format(serial, date)
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    file_count = len(os.listdir(dirname))

    meter_data = create_or_get_meters()
    entry = {
        "serialNumber": serial,
        "timeLastCommunicated": now_to_second().isoformat(),
        "countOfFilesAvailable": file_count,
        "latestFile": date,
    }

    meter_data[serial] = entry
    save_meter_data(meter_data)

    return data


def convert_to_pipeline_format(data):
    # this is the ProcessingPayload format from the pipeline.
    meter = {}
    meter["serialNumber"] = data["serial"]

    unit_of_work = {}
    unit_of_work["serialNumber"] = data["serial"]
    # really not sure about this - how do I know ?
    unit_of_work["payloadDate"] = "{}T00:00:00+12:00".format(data["reading_day"])

    datastreams = []
    for name, reading_data in data["datastreams"].items():
        datastream = {}
        datastream["name"] = name
        datastream[
            "interval"
        ] = 5  # TODO this should come from metadata but is missing.

        readings = []
        for timestamp, value in reading_data.items():
            readings.append({"timestamp": timestamp, "value": value})
        datastream["readings"] = readings
        datastreams.append(datastream)

    unit_of_work["dataStreams"] = datastreams
    converted_data = {"meter": meter, "unitOfWork": unit_of_work}

    return converted_data


def get_headers():
    return {
        # 'x-api-key': tempest_secrets.API_KEY,
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }


def remove_metadata(data):
    data.pop("metadata")
    return data


def upload_to_pipeline(serial, date, data):
    converted_data = (
        convert_to_pipeline_format(data)
        if CONVERT_TO_PIPELINE
        else remove_metadata(data)
    )
    # url = tempest_secrets.PIPELINE_URL
    url = (
        PIPELINE_URL + "/ingestions/processing"
        if CONVERT_TO_PIPELINE
        else PIPELINE_URL + "/ingestions/picos"
    )
    headers = get_headers()
    log("uploading {}/{} to pipeline @ {} : {}".format(serial, date, url, headers))
    response = requests.post(url, json=converted_data, headers=headers)
    log(response)


def update(data):
    serial = data["serial"]
    date = data["reading_day"]
    log("updating {}@{}".format(serial, date))
    save_all_data(serial, date, data)
    upload_to_pipeline(serial, date, data)


def get_status():

    heartbeats = get_heartbeats()
    active_meter_count = 0
    inactive_meter_count = 0
    for heartbeat in heartbeats:
        elapsed = heartbeat['elapsedSeconds']
        if elapsed > (60 * 60): # not heard from in 1 hour
            inactive_meter_count = inactive_meter_count + 1
        else:
            active_meter_count = active_meter_count + 1

    time_to_upload = '?'
    return {
        'activeMeters': active_meter_count,
        'inactiveMeters': inactive_meter_count,
        'timeToUpload': time_to_upload
    }

# startup
if __name__ == "__main__":
    filename = "tempest_server.log"
    if os.path.exists(filename):
        os.remove(filename)
