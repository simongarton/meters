import time
import json

from pico_oled_1_3_driver import OLED_1inch3

# light version, no IP
def load_config():
    with open('config.json', 'r') as config_file:
        data = json.load(config_file)
    return data

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
