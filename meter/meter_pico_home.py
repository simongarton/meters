

# support for home - reading my home usage from a Mercury energy export

# take a look at /data and you'll see the original file home-2022.csv, which is
# exactly the same format as you download, only removing the first five lines which
# are just metadata.
#
# there are scripts in there to split that file iinto


# add these

import time

YEAR = 2022

# add this

def get_reading_from_file(month, day, hour, min, divisor):
    date = '{:04d}-{:02d}-{:02d}'.format(YEAR, month, day)
    month = '{:04d}-{:02d}'.format(YEAR, month)
    time = '{:02d}:{:02d}'.format(hour, min)
    filename = 'months/{}.csv'.format(month)
    with open(filename, 'r') as csvfile:
        while True:
            row = csvfile.readline()
            if not row:
                break
            row_data = row.split(',')
            if row_data[0] == date:
                if row_data[1] == time:
                    return round(1000 * float(row_data[2]) / divisor) / 1000.0

# and change this method

def generate_reading(usable_time, config, channel_name, channel_factor):
    month = usable_time[1]
    day = usable_time[2]
    hour = usable_time[3]
    min = usable_time[4]
    min30 = (min // 30) * 30
    return get_reading_from_file(month, day, hour, min30, 6)


# these two are for testing

def get_ureading(reading_time):
    min30 = (reading_time.tm_min // 30) * 30
    return get_reading_from_file(reading_time.tm_mon, reading_time.tm_mday, reading_time.tm_hour, min30, 6)

now = time.localtime()
print(get_ureading(now))
