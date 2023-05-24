
import requests

# A fake / decorator module to mimic what I would have in a MicroPython environment

def post(url, headers, json):
    print('urequests to {} to {}'.format(url, json))
    requests.post(url, headers=headers, json=json)