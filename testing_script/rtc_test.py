import busio
import adafruit_pcf8523
import datetime
import time
from board import *

#References
#https://github.com/adafruit/Adafruit_CircuitPython_PCF8523

i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)
x = datetime.datetime.now()
print(x)
# time struct: (year, month, month_day, hour, min, sec, week_day {Monday=0}, year_day, is_daylightsaving?)
# run this once with the line below uncommented to reset rtc to current date time
#rtc.datetime = time.struct_time((x.year, x.month, x.day, x.hour, x.minute, x.second, 0,  -1, -1))

#Testing
t = rtc.datetime
try: 
    print(x)
    print(t)
    print(t.tm_hour,t.tm_min)
    print("Is it in power savings mode?")
    print(t.tm_hour > 16 or t.tm_hour < 9)
    print("\n")
except:
    curr_dt = rtc.datetime
    curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
    print(curr_time_min)
    print(curr_dt.tm_yday)
