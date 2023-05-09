
import requests

# A fake / decorator module to mimic what I would have in a MicroPython environment

def post(url, json):
    print('urequests to {} to {}'.format(url, json))
    requests.post(url, json=json)