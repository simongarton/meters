import requests
import time
import datetime

URL = 'http://192.168.86.51:8002/upload'

def upload():
    print('Posting at {} to {}'.format(datetime.datetime.now(), URL))
    requests.post(URL)

def run():
    while True:
        now = datetime.datetime.now()
        if (now.minute % 10) == 0:
            upload()
        else:
            print('snoozing at {}', datetime.datetime.now())
        time.sleep(60)


if __name__ == '__main__':
    run()