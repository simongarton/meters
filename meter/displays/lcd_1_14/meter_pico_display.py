import time
import json
import random

# LCD_1inch14 240 x 135 and 16 bit color

from pico_lcd_1_14_driver import LCD_1inch14

display = LCD_1inch14()

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

# lcd_color

def lcd_color(red, green, blue):
    # 565 : 5 bits of red, 6 bits of green, 5 bits of blue
    # 2^5 = 32
    # 2^6 = 64
    # 32 * 64 = 2048

    r1 = red >> 5
    g1 = green >> 5
    b1 = blue >> 5
    # this seems to work - the gradients are right - but doesn't really mach up the 565 I was expecting
    rgb565 = r1 * 32 + g1 + b1 * 1024
    # print('{},{},{} -> {},{},{} = {}'.format(
    #     red,
    #     green,
    #     blue,
    #     r1,
    #     g1,
    #     b1,
    #     hex(rgb565)
    # ))
    return rgb565

def lcd_color_index(index):
    i = index % 6
    if i == 0:
        return lcd_color(255,0,0)
    if i == 1:
        return lcd_color(0,255,0)
    if i == 2:
        return lcd_color(0,0,255)
    if i == 3:
        return lcd_color(255,0,255)
    if i == 4:
        return lcd_color(255,255,0)
    if i == 5:
        return lcd_color(0,255,255)

# splash screen

def gradient():
    for x in range(0, 240):
        fraction = (x + 1) / 240
        color_fraction = int(255 * fraction)
        g = 0
        r = 255 - color_fraction
        b = color_fraction
        color = lcd_color(r,g,b)
        # print("{}:{},{},{} -> {}".format(x, r, g, b, color))
        display.line(x, 0, x, 135, color)
        # display.fill_rect(0, 0, 240, 135, color)
        # display.show()
    display.show()
    time.sleep(1000)

def splash_screen(title):
    global display
    display.fill(0x0000) 
    display.show()
    display.rect(0,0,240,135,display.white)
    display.show()
    wait = 0.01
    time.sleep(wait)
    # gradient()
    display.fill_rect(20,25,20,20,lcd_color(255,0,0))
    time.sleep(wait)
    display.show()
    display.fill_rect(50,25,20,20,lcd_color(0,255,0))
    time.sleep(wait)
    display.show()
    display.fill_rect(80,25,20,20,lcd_color(0,0,255))
    time.sleep(wait)
    display.show()
    display.fill_rect(110,25,20,20,lcd_color(255,0,255))
    time.sleep(wait)
    display.show()
    display.fill_rect(140,25,20,20,lcd_color(0,255,255))
    time.sleep(wait)
    display.show()
    display.fill_rect(170,25,20,20,lcd_color(255,255,0))
    time.sleep(wait)
    display.show()
    display.fill_rect(200,25,20,20,lcd_color(128,128,128))
    time.sleep(wait)
    display.show()
    for y in range(2):
        for x in range(7):
            display.fill_rect(20 + x * 30,25 + (y + 1) * 30,20,20,lcd_color(random.randint(0,255),random.randint(0,255),random.randint(0,255)))
            display.show()
            time.sleep(wait)
    display.show()
    time.sleep(5)
    display.fill(0x0000) 
    display.text(title,20,55,display.white)
    display.show()
    time.sleep(3)
    display.fill(0x0000) 
    display.show()


# single message

def display_single_message(message):
    global display
    display.fill(0x0000) 
    display.text(message,20,55,display.white)
    display.show()

# last value

def display_last_values(timestamp, readings, interval):
    global display
    display.fill(0x0000) 
    display.text(timestamp,160,5,display.white)
    index = 0
    if len(readings) == 0:
        display.text('no readings yet',20,55,display.white)
    for (channel_name, value) in readings:
        display.text('{} : {}'.format(channel_name, value),5,15 + (10 * index),lcd_color_index(index))
        index = index + 1
    display.show()

# bar chart

def display_bar_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 

    if len(readings) == 0:
        display.text('no readings yet',20,55,display.white)
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
    scale = 200 / max

    index = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        display.text('{}'.format(channel_name[0]),1,5 + (10 * index),display.white)
        scaled_value = int(sums[channel_name] * scale)
        display.rect(15, 5 + (10 * index), scaled_value, 8,lcd_color_index(index), True)
        index = index + 1
    display.show()


# line chart

def display_line_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 

    if len(readings) == 0:
        display.text('no readings yet',20,55,display.white)
        display.show()
        return
    
    max = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        for reading in reading_list:
            if reading > max:
                max = reading
    scale = 135 / max
    
    index = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        x = 0
        display.fill(0x0000) 
        display.text('{}'.format(channel_name),5,5,display.white)
        last_x1 = None
        last_y1 = None
        for reading in reading_list:
            x1 = int(x * 240 / 288)
            y1 = 135 - int(reading * scale)
            if last_x1 != None:
                display.line(last_x1, last_y1, x1, y1,lcd_color_index(index))
            last_x1 = x1
            last_y1 = y1
            x = x + 1
        display.show()
        time.sleep(1)
        index = index + 1

    display.fill(0x0000) 
    display.text('{}'.format('All'),5,5,display.white)
    index = 0
    for (channel_name, value) in readings:
        reading_list = load_readings(channel_name)
        x = 0
        last_x1 = None
        last_y1 = None
        for reading in reading_list:
            x1 = int(x * 240 / 288)
            y1 = 135 - int(reading * scale)
            if last_x1 != None:
                display.line(last_x1, last_y1, x1, y1,lcd_color_index(index))
            last_x1 = x1
            last_y1 = y1
            x = x + 1
        index = index + 1
    display.show()

# totals

def display_total_chart(timestamp, readings, interval):
    global display
    display.fill(0x0000) 
    display.text('{}'.format('All'),5,5,display.white)

    if len(readings) == 0:
        display.text('no readings yet',20,55,display.white)
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
    scale = 135 / max
    
    x = 0
    for reading in totals:
        x1 = int(x * 240 / 288)
        y1 = int(reading * scale)
        fraction = (x + 1) / 288
        color_fraction = int(255 * fraction)
        r = 0
        g = 255 - color_fraction
        b = color_fraction
        # print("{}:{},{},{}".format(x, r, g, b))
        # display.line(x1, 135, x1, 135 - y1, lcd_color(r,g,b))
        display.line(x1, 135, x1, 135 - y1, lcd_color(127, 127, 127))
        x = x + 1
    display.show()