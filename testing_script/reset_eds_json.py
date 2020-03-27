import json
import busio
import adafruit_pcf8523
import time
from board import *

# This script is when you want to change the schedule of the FTU
# After changing, the eds.json files need to be reseted
# By reseting, change all is_activated to False, and record_dt to current daytimes

# get current dt
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)
dt = rtc.datetime

# load the json file
with open('/home/pi/Desktop/eds.json', 'r') as file:
    json_file = json.load(file)
# reset all is_activated into false
eds_names = ['eds1','eds2','eds3','eds4','eds5']
for x in eds_names:
    json_file[x].update({
        'is_activated':False,
        'record_dt': dt
    })
# re-write the new json file
with open('/home/pi/Desktop/eds.json', 'w+') as file:
    json.dump(json_file, file)