import busio
import adafruit_pcf8523
import time
from board import *
import json

i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

time = rtc.datetime

class Panel:
    def __init__(self, name, frequency, m_time, a_time):
        self.panel_type = name
        self.frequency = frequency # how many activations per day/2 days
        self.measurement_time = m_time # in minutes
        self.activation_time = a_time # in minutes
        self.is_activated = False

    def reset_json_files(self):
        pass
    
    def activation_record(self, dt):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        eds = {
            'panel':self.panel_type,
            'is_activated':True,
            'activation_time':a_time,
            'activation_dt':dt,
        }
        with open('activation_record.json', 'w') as file:
            json.dump(eds, file)
        return True
    
    def measurement_record(self, dt):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        eds = {
            'panel':self.panel_type,
            'is_activated':True,
            'activation_time':m_time,
            'activation_date':date
        }
        with open('measurement_record.json', 'w') as file:
            json.dump(eds, file)
        return False
    
    def check_frequency(self, mode, dt)
        file_name = mode + "_record.json"
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        with open(file_name, 'r') as file:
            json_file = json.load(file)
        
        current_day = day_of_year(dt)
        activation_day = day_of_year(json_file['activation_dt'])
        #already met desired frequency for activation
        if current_day - activation_day == self.frequency:
            json_file.update({
                'activation_dt':dt
            })
            with open('activation_record.json', 'w') as file:
                json.dump(json_file, file)
            return True
        else:
            json_file.update({
                'is_activated':False
            })
            with open('activation_record.json', 'w') as file:
                json.dump(json_file, file)
            return False

    def check_leap_year (self, dt):
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
    
    def day_of_year(self, dt):
        if check_leap_year(dt) == True:
            month_days = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        else:
            month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        
        return month_days[dt.tm_mon-1] + dt.tm_mday