import busio
import adafruit_pcf8523
import time
from board import *

#References
#https://github.com/adafruit/Adafruit_CircuitPython_PCF8523

i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

# time struct: (year, month, month_day, hour, min, sec, week_day {Monday=0}, year_day, is_daylightsaving?)
# run this once with the line below uncommented
#rtc.datetime = time.struct_time((2019,7,5,12,8,0,0,173,-1))

#Testing
t = rtc.datetime
print(t)
print(t.tm_hour, t.tm_min)
print("\n")
curr_dt = rtc.datetime
curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
print(curr_time_min)