import time
import network
import urequests
import json

OFFSET_HOURS = 12
OFFSET = '+12:00'


def convert_time_to_local(struct_time):
    # cross reference add_delta()
    seconds = time.mktime(struct_time)
    seconds = seconds + OFFSET_HOURS * 60 * 60
    return time.localtime(seconds)


def localtime():
    return convert_time_to_local(time.localtime())


def strftime_time(struct_time):
    # change this one depending on what output you want.
    # Remember the Pico is not daylight savings aware
    return strftime_time_local(struct_time)


def strftime_time_local(struct_time):
    return "{:04.0f}-{:02.0f}-{:02.0f}T{:02.0f}:{:02.0f}:{:02.0f}{}".format(
        struct_time[0],
        struct_time[1],
        struct_time[2],
        struct_time[3],
        struct_time[4],
        struct_time[5],
        OFFSET,
    )


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True
    while True:
        print("connecting to {}".format(secrets.SSID))
        wlan.connect(secrets.SSID, secrets.PASSWORD)
        print("connected to wifi : {}".format(wlan.isconnected()))
        if wlan.isconnected():
            return True
        time.sleep(5)


def heartbeat(config):
    connect()
    serial = config["serial"] if "serial" in config else "no-serial-number"
    ip = config["ip"] if "ip" in config else "no-ip"
    heartbeat_data = {
        "serial": serial,
        "ip": ip,
        "timestamp": strftime_time(localtime()),
    }

    url = config["tempest_url"]
    api_key = config["tempest_api_key"]
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    response = urequests.post(url + "heartbeat", headers=headers, json=heartbeat_data)
    print(response.status_code)


def load_config():
    with open("config.json", "r") as config_file:
        data = json.load(config_file)
    try:
        data["ip"] = get_ip()
    except:
        data["ip"] = "0.0.0.0"
    return data

def get_ip():
    wlan = network.WLAN(network.STA_IF)
    return wlan.ifconfig()[2]


def run():
    config = load_config()
    heartbeat(config)

if __name__ == '__main__':
    run()