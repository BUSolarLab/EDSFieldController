import busio
import adafruit_pcf8523
import time
from board import *
import json
from os import path

# declare RTC
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)
t = rtc.datetime

# run the test

while True:

    current_dt=rtc.datetime
    if current_dt.tm_hour > 17 or current_dt.tm_hour < 9:
        day = False
    else:
        day = True

    if day:
        t = rtc.datetime
        print(t)
        time.sleep(60*15)