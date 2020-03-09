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

# declare frequency
frequency = 2

# functions
def time_record(dt):
    date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
    eds = {
        'record':dt,
    }
    with open('./record.json', 'w') as file:
        json.dump(eds, file)
    return True

def check_leap_year(dt):
    year = dt.tm_year
    if (year % 4) == 0:
        if (year % 100) == 0:
            if (year % 400) == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def day_of_year(dt):
    if check_leap_year(dt) == True:
        month_days = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    else:
        month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    
    return month_days[dt.tm_mon-1] + dt.tm_mday

def check_frequency(dt):
    if not path.exists("./record.json"):
        return True
    else:
        file_name = "./record.json"
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        with open(file_name, 'r') as file:
            json_file = json.load(file)
        
        current_day = day_of_year(dt)
        activation_day = day_of_year(time.struct_time(tuple(json_file['record'])))
        #already met desired frequency for activation
        if current_day - activation_day == frequency:
            json_file.update({
                'record':dt
            })
            with open('./record.json', 'w') as file:
                json.dump(json_file, file)
            return True
        else:
            return False

# run the test
while True:
    print("Start Testing, Recording Frequency: " + str(frequency) + " days")
    t = rtc.datetime
    if check_frequency(t) == True:
        time_record(t)
        print("Recorded Time")
