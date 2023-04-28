import time
import json

# this is shell version, with the right methods but no specific display

# light version, no IP
def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    return data

def file_exists(filename):
    try:
        with open(filename, 'r') as file:
            pass
        return True
    except:
        return False
    
def load_readings(channel_name):
    filename = 'charts/{}.csv'.format(channel_name)
    if not file_exists(filename):
        return []
    readings = []
    with open(filename, 'r') as input:
        new_readings = input.readlines()
        for new_reading in new_readings:
            readings.append(float(new_reading))
    return readings

# splash screen

def splash_screen(title):
    print('splash_screen : {}'.format(title))

# single message

def display_single_message(message):
    print('display_single_message : {}'.format(message))

# last value

def display_last_values(timestamp, readings, interval):
    print('display_last_values : {}/{}/{}'.format(timestamp, len(readings), interval))

# bar chart

def display_bar_chart(timestamp, readings, interval):
    print('display_bar_chart : {}/{}/{}'.format(timestamp, len(readings), interval))

# line chart

def display_line_chart(timestamp, readings, interval):
    print('display_line_chart : {}/{}/{}'.format(timestamp, len(readings), interval))

# total chart

def display_total_chart(timestamp, readings, interval):
    print('display_total_chart : {}/{}/{}'.format(timestamp, len(readings), interval))
