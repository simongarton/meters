import datetime
import time
import csv

# takes the mercury energy style file and reads it for a date / time that
# matches the month, day, hour and the 30th minute.

# this is 1Mb in size - will it work with a Pico ?

# TYPE,DATE,START TIME,END TIME,USAGE,UNITS,COST,NOTES
# Electricity usage,2022-01-01,00:00,00:29,1.65,kWh,$0.32,
# Electricity usage,2022-01-01,00:30,00:59,1.93,kWh,$0.38,

FILENAME = 'home-2022.csv'
YEAR = 2022


def split_datetime(reading_time):
    return (
        reading_time.year,
        reading_time.month,
        reading_time.day,
        reading_time.hour,
        reading_time.minute,
        reading_time.second,
    )


def get_reading_from_file(month, day, hour, min, divisor):
    date = '{:04d}-{:02d}-{:02d}'.format(YEAR, month, day)
    time = '{:02d}:{:02d}'.format(hour, min)
    print(date + ',' + time)
    with open(FILENAME, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[1] == date:
                if row[2] == time:
                    return  round(1000 * float(row[4]) / divisor) / 1000.0


def get_reading(reading_time):
    (year, month, day, hour, min, second) = split_datetime(reading_time)
    min30 = (min // 30) * 30
    return get_reading_from_file(month, day, hour, min30, 6)


def get_ureading(reading_time):
    min30 = (reading_time.tm_min // 30) * 30
    return get_reading_from_file(reading_time.tm_mon, reading_time.tm_mday, reading_time.tm_hour, min30, 6)

# full python
# now = datetime.datetime.now()
# print(get_reading(now))

# micropython
now = time.localtime()
print(get_ureading(now))
