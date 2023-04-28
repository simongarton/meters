import time
import json

# OLED_1inch3 128 x 64

from pico_oled_1_3_driver import OLED_1inch3

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
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        splash_screen_oled_1_3(title)
    if config['display'] == 'lcd-1.14':
        splash_screen_lcd_1_14(title)
        

def splash_screen_oled_1_3(title):
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 
    OLED.show()
    OLED.rect(0,0,128,64,OLED.white)
    time.sleep(0.1)
    OLED.show()
    OLED.rect(10,22,20,20,OLED.white)
    time.sleep(0.1)
    OLED.show()
    OLED.fill_rect(40,22,20,20,OLED.white)
    time.sleep(0.1)
    OLED.show()
    OLED.rect(70,22,20,20,OLED.white)
    time.sleep(0.1)
    OLED.show()
    OLED.fill_rect(100,22,20,20,OLED.white)
    time.sleep(0.1)
    OLED.show()
    time.sleep(1)
    OLED.fill(0x0000) 
    OLED.text(title,10,27,OLED.white)
    OLED.show()
    time.sleep(3)
    OLED.fill(0xffff) 
    OLED.show()
    time.sleep(0.2)
    OLED.fill(0x0000) 
    OLED.show()


def splash_screen_lcd_1_14():
    pass


# single message

def display_single_message(message):
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        display_single_message_oled_1_3(message)


def display_single_message_oled_1_3(message):
    # each time ? global ?
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 
    OLED.text(message,5,27,OLED.white)
    OLED.show()


# last value

def display_last_values(time, readings, interval):
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        display_last_values(time, readings, interval)


def display_last_values(time, readings, interval):
    # each time ? global ?
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 
    OLED.text(time,60,5,OLED.white)
    index = 0
    if len(readings) == 0:
        OLED.text('no readings yet',5,25,OLED.white)
    for (channel_name, value) in readings:
        OLED.text('{} : {}'.format(channel_name, value),5,15 + (10 * index),OLED.white)
        index = index + 1
    OLED.show()

# bar chart

def display_bar_chart(time, readings, interval):
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        display_bar_chart(time, readings, interval)


def display_bar_chart(time, readings, interval):
    # each time ? global ?
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 

    if len(readings) == 0:
        OLED.text('no readings yet',5,25,OLED.white)
        OLED.show()
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
        OLED.text('{}'.format(channel_name[0]),1,5 + (10 * index),OLED.white)
        scaled_value = int(sums[channel_name] * scale)
        OLED.rect(15, 5 + (10 * index), scaled_value, 8, OLED.white, True)
        index = index + 1
    OLED.show()


# line chart

def display_line_chart(time, readings, interval):
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        display_line_chart(time, readings, interval)


def display_line_chart(time, readings, interval):
    # each time ? global ?
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 

    if len(readings) == 0:
        OLED.text('no readings yet',5,25,OLED.white)
        OLED.show()
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
        for reading in reading_list:
            x1 = int(x * 128 / 288)
            y1 = int(reading * scale)
            OLED.pixel(x1, 64 - y1, OLED.white)
            x = x + 1
    OLED.show()

# totals

def display_total_chart(time, readings, interval):
    config = load_config()
    if not 'display' in config:
        return
    if config['display'] == 'oled-1.3':
        display_total_chart(time, readings, interval)


def display_total_chart(time, readings, interval):
    # each time ? global ?
    OLED = OLED_1inch3()
    OLED.fill(0x0000) 

    if len(readings) == 0:
        OLED.text('no readings yet',5,25,OLED.white)
        OLED.show()
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
        OLED.line(x1, 64, x1, 64 - y1, OLED.white)
        x = x + 1
    OLED.show()