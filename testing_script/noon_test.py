import busio
import adafruit_pcf8523
import time
from board import *
from math import floor, ceil, cos, sin
from numpy import deg2rad

def get_solar_time(gmt_off, dt, longitude, latitude):
    # implementation adapted from https://sciencing.com/calculate-solar-time-8612288.html
    A = 15 * gmt_off
    B = (dt.tm_yday - 81) * 360 / 365
    C = 9.87 * sin(deg2rad(2 * B)) - 7.53 * cos(deg2rad(B)) - 1.58 * sin(deg2rad(B))
    D = 4 * (A - longitude) + C
    # return solar time offset in minutes
    return D

def print_time(dt):
    return (str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec) + '')


#Days per month
Y_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

# RTC setup
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)


while True:
    # get solar offset
    current_time = rtc.datetime
    longitude = -71.05
    gmt_offset = -5
    latitude = 1
    solar_offset = ceil(get_solar_time(gmt_offset, current_time, longitude, latitude) * 100)/100

    # get solar noon
    curr_dt = rtc.datetime
    yday = Y_DAYS[curr_dt.tm_mon - 1] + curr_dt.tm_mday
    solar_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60 + solar_offset
    curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
    solar_noon_min = 720 + solar_offset

    #testing purposes
    with open('test.txt', 'a+') as f:
            f.writelines(print_time(curr_dt))
            f.writelines(" - Solar Noon Time in Minutes: " + str(solar_noon_min))
            f.writelines("\n")


    # if within 60 seconds/30 min of solar noon, run measurements
    if abs(solar_noon_min - curr_time_min) < 30:
        with open('test.txt', 'a+') as f:
            f.writelines(print_time(curr_dt))
            f.writelines(" - Solar Noon Time in Minutes: " + str(solar_noon_min))
            f.writelines("\n")

    time.sleep(5)