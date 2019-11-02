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

#Days per month
Y_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

# RTC setup
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

# get solar offset
current_time = rtc.datetime
longitude = -71.05
gmt_offset = -4
latitude = 1
solar_offset = ceil(get_solar_time(gmt_offset, current_time, longitude, latitude) * 100)/100

# get solar noon
curr_dt = rtc.datetime
yday = Y_DAYS[curr_dt.tm_mon - 1] + curr_dt.tm_mday
solar_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60 + solar_offset

# if within 60 seconds of solar noon, run measurements
tres = abs(720 - solar_time_min)
if tres < 1.0:
    print("Hello")