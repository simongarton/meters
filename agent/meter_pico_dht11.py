
# This file has the changes you need to extend meter_pico.py to read from a DHT11 temp/humidity sensor.

# You'll need the dht.py driver.

# import changes
from machine import Pin
from dht import DHT11

# set this up as a global - look at which pin you are setting up
sensor = DHT11(Pin(0, Pin.OUT, Pin.PULL_DOWN))

# make sure your config has two datastreams, temperature and humidity

# and then the new generate_reading() method 
def generate_reading(usable_time, config, channel_name, channel_factor):
    working_hour = usable_time[3]

    global sensor
    try:
        if channel_name.lower() == 'temperature':
            time.sleep(2) # needed to give the sensor a chance
            return sensor.temperature
        if channel_name.lower() == 'humidity':
            time.sleep(2) # needed to give the sensor a chance
            return sensor.humidity
        print('unknown sensor channel {}'.format(channel_name))
    except Exception as e:
        print('error with sensor : {}'.format(e))
    return 0
