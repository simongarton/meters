
import time as thing

def sleep(n):
    thing.sleep(n)

def localtime(n=None):
    return thing.localtime(n)


def convert_micro_to_full(struct_time):
    year = struct_time[0]
    month = struct_time[1]
    day = struct_time[2]
    hour = struct_time[3]
    minute = struct_time[4]
    second = struct_time[5]
    wday = struct_time[6]
    yday = struct_time[7]
    is_dst = 0   
    return (
        year,
        month,
        day,
        hour,
        minute,
        second,
        wday,
        yday,
        is_dst
    )

def mktime(struct_time):
    fixed_tuple = convert_micro_to_full(struct_time)
    return thing.mktime(fixed_tuple)


def utime():
    return thing.time()