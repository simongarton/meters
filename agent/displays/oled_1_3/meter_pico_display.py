import time
import json

# OLED_1inch3 128 x 64, monocolor

from pico_old_1_3_driver import OLED_1inch3

display = OLED_1inch3()

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
    global display
    display.fill(0x0000) 
    display.show()
    display.rect(0,0,128,64,display.white)
    time.sleep(0.1)
    display.show()
    display.rect(10,22,20,20,display.white)
    time.sleep(0.1)
    display.show()
    display.fill_rect(40,22,20,20,display.white)
    time.sleep(0.1)
    display.show()
    display.rect(70,22,20,20,display.white)
    time.sleep(0.1)
    display.show()
    display.fill_rect(100,22,20,20,display.white)
    time.sleep(0.1)
    display.show()
    time.sleep(1)
    display.fill(0x0000) 
    display.text(title,10,27,display.white)
    display.show()
    time.sleep(3)
    display.fill(0xffff) 
    display.show()
    time.sleep(0.2)
    display.fill(0x0000) 
    display.show()


# single message

def display_single_message(message):
    global display
    display.fill(0x0000) 
    display.text(message,5,27,display.white)
    display.show()

# last value

def display_last_values(timestamp, readings, interval):
    global display
    display.fill(0x0000) 
    display.text(timestamp,60,5,display.white)
    index = 0
    if len(readings) == 0:
        display.text('no readings yet',5,25,display.white)
    for (channel_name, value) in readings:
        display.text('{} : {}'.format(channel_name, value),5,15 + (10 * index),display.white)
        index = index + 1
    display.show()

# bar chart

def display_bar_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 

    if len(readings) == 0:
        display.text('no readings yet',5,25,display.white)
        display.show()
        return

    max = 0
    sums = {}
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        sum = 0
        for reading in reading_list:
            sum = sum + reading
        sums[channel_name] = sum
        if max < sum:
            max = sum
    scale = 100 / max

    index = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        display.text('{}'.format(channel_name[0]),1,5 + (10 * index),display.white)
        scaled_value = int(sums[channel_name] * scale)
        display.rect(15, 5 + (10 * index), scaled_value, 8, display.white, True)
        index = index + 1
    display.show()


# line chart

def display_line_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 

    if len(readings) == 0:
        display.text('no readings yet',5,25,display.white)
        display.show()
        return
    
    max = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        for reading in reading_list:
            if reading > max:
                max = reading
    scale = 64 / max
    
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        x = 0
        display.fill(0x0000) 
        display.text('{}'.format(channel_name),5,5,display.white)
        last_x1 = None
        last_y1 = None
        for reading in reading_list:
            x1 = int(x * 128 / 288)
            y1 = 64 - int(reading * scale)
            if last_x1 != None:
                display.line(last_x1, last_y1, x1, y1, display.white)
            last_x1 = x1
            last_y1 = y1
            x = x + 1
        display.show()
        time.sleep(1)

    display.fill(0x0000) 
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        x = 0
        last_x1 = None
        last_y1 = None
        for reading in reading_list:
            x1 = int(x * 128 / 288)
            y1 = 64 - int(reading * scale)
            if last_x1 != None:
                display.line(last_x1, last_y1, x1, y1, display.white)
            last_x1 = x1
            last_y1 = y1
            x = x + 1
    display.show()

# totals

def display_total_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 

    if len(readings) == 0:
        display.text('no readings yet',5,25,display.white)
        display.show()
        return
    
    max = 0
    totals = []
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        if len(totals) == 0:
            totals = reading_list
        else:
            for i in range(len(totals)):
                reading = reading_list[i]
                totals[i] = totals[i] + reading
                if totals[i] > max:
                    max = totals[i]
    scale = 64 / max
    
    x = 0
    for reading in totals:
        x1 = int(x * 128 / 288)
        y1 = int(reading * scale)
        display.line(x1, 64, x1, 64 - y1, display.white)
        x = x + 1
    display.show()