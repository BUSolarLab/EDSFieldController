'''
=============================
Title: Configuration File Management - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''
from os import path
from math import cos, sin
from numpy import deg2rad
import json
import time
import subprocess

DEFAULT_CONFIG_PARAM = {
    # EDS Panels for power supply activation
    'EDS1': 4,
    'EDS2': 17,
    'EDS3': 6,
    'EDS4': 19,
    'EDS5': 26,
    'EDS6': 27,
    # EDS nd CTRL Panels measurement
    'EDS1PV': 7,
    'EDS2PV': 8,
    'EDS3PV': 12,
    'EDS4PV': 16,
    'EDS5PV': 20,
    'EDS6PV': 21,
    'CTRL1PV': 15,
    'CTRL2PV': 23,
    'CTRLIDS': [1, 2],
    # for measurement loop
    'PANELIDS':['eds1','eds2','eds3','eds4','eds5','ctrl1','ctrl2'],
    'EDSIDS': ['eds1','eds2','eds3','eds4','eds5'],
    'CTRLIDS': ['ctrl1','ctrl2'],
    # testing requirements
    'maxTemperatureCelsius': 40,
    'minTemperatureCelsius': 10,
    'maxRelativeHumidity': 60,
    'minRelativeHumidity': 5,
    'testDurationSeconds': 60, # 1 minute
    'testWindowSeconds': 2700,
    # indicators/switches
    'outPinLEDGreen': 5,
    'outPinLEDRed': 13,
    'inPinManualActivate': 22,
    'manualEDSNumber': 5, #EDS 5
    'ADC': 25,
    'solarChargerEDSNumber': 6,
    # location data
    'degLongitude': -71.05,
    'offsetGMT': -5,
    }

# dictionary for panel measurement
PANEL_DATA = {
    'eds1':{
        'name':'EDS1',
        'num':1,
        'type':'eds',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0,
        'frequency':1,
        'schedule':['SN'] #in minutes
    },
    'eds2':{
        'name':'EDS2',
        'num':2,
        'type':'eds',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0,
        'frequency':0,
        'schedule':['1080', '1085'] #in minutes.
    },
    'eds3':{
        'name':'EDS3',
        'num':3,
        'type':'eds',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0,
        'frequency':0,
        'schedule':['1090'] #in minutes, 10.00AM
    },
    'eds4':{
        'name':'EDS4',
        'num':4,
        'type':'eds',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0,
        'frequency':1,
        'schedule':['660'] #in minutes, 11:00AM, 13:00PM
    },
    'eds5':{
        'name':'EDS5',
        'num':5,
        'type':'eds',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0,
        'frequency':2,
        'schedule':['780'] #in minutes, 1:00PM, 10:00AM
    },
    'ctrl1':{
        'name':'CTRL1',
        'num':1,
        'type':'ctrl',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':'N/A',
        'scc_pre':0,
        'scc_post':'N/A',
        'pwr_pre':0,
        'pwr_post':'N/A',
        'pr_pre':0,
        'pr_post':'N/A',
        'sr_pre':0,
        'sr_post':'N/A',
        'frequency':'', # No Determined Frequency
        'schedule':[] # No Determined Schedule
    },
    'ctrl2':{
        'name':'CTRL2',
        'num':2,
        'type':'ctrl',
        'date_time':'',
        'temp':0,
        'humid':0,
        'gpoa':0,
        'ocv_pre':0,
        'ocv_post':'N/A',
        'scc_pre':0,
        'scc_post':'N/A',
        'pwr_pre':0,
        'pwr_post':'N/A',
        'pr_pre':0,
        'pr_post':'N/A',
        'sr_pre':0,
        'sr_post':'N/A',
        'frequency':'', # No Determined Frequency
        'schedule':[] # No Determined Schedule
    }
}

'''
Static master class
Functionality:
1) Contains and maintains static global values that will remain UNCHANGED
2) Contains default configuration file values for reference
'''

class StaticMaster:
    
    def __init__(self):
        # immutable constants are not put in the dictionary
        self.config_dictionary = DEFAULT_CONFIG_PARAM
        self.panel_data = PANEL_DATA

    def get_config(self):
        # returns config dictionary for other functions to use
        return self.config_dictionary

    def get_panel_data(self):
        # returns panel data template for measurements
        return self.panel_data


'''
Schedule class
Functionality:
1) Check activation/measurement frequency
2) Check with scheduled time for activation/measurement
3) Stores this information in json file in Desktop of RasPi
'''
class ScheduleMaster:
    def __init__(self, name, frequency, schedule, longitude, gmt_off):
        self.panel_type = name
        self.frequency = frequency # how many activations per day/2 days
        self.schedule_time = schedule # in minutes

        # for calculating solar noon
        self.longitude = longitude
        self.gmt_off = gmt_off

    def check_json_file(self, dt):
        if not path.exists('/home/pi/Desktop/eds.json'):
            eds = {
                'eds1':{
                    'is_activated':False,
                    'record_dt': dt
                },
                'eds2':{
                    'is_activated':False,
                    'record_dt': dt
                },
                'eds3':{
                    'is_activated':False,
                    'record_dt': dt
                },
                'eds4':{
                    'is_activated':False,
                    'record_dt': dt
                },
                'eds5':{
                    'is_activated':False,
                    'record_dt': dt
                }
            }
            with open('/home/pi/Desktop/eds.json', 'w+') as file:
                json.dump(eds, file)
            
            return True
    
    def check_frequency(self,name,dt):
        # check if json file exists, if it doesnt, then return True to run sequence
        '''
        TO EDIT: IF record_dt is '', then return True
        '''
        # check if no json file in the desktop directory
        self.check_json_file(dt)

        # load the json file
        with open('/home/pi/Desktop/eds.json', 'r') as file:
            json_file = json.load(file)

        # check for frequency confirmation, also check if it is first activation, meaning record in json will be blank
        current_day = self.day_of_year(dt)
        activation_day = self.day_of_year(time.struct_time(tuple(json_file[name]['record_dt'])))

        # delete the file, avoid permission problems
        subprocess.call("sudo rm /home/pi/Desktop/eds.json", shell=True)

        # already met desired frequency for activation
        if current_day - activation_day == self.frequency:
            json_file[name].update({
                'is_activated':True,
                'record_dt':dt
            })
            with open('/home/pi/Desktop/eds.json', 'w') as file:
                json.dump(json_file, file)
            return True
        else:
            # don't change the record_dt since did not meet frequency check
            json_file[name].update({
                'is_activated':False
            })
            with open('/home/pi/Desktop/eds.json', 'w') as file:
                json.dump(json_file, file)
            return False
        '''
        try: 

        except TypeError:
            # this is to handle the first entry, where record_dt was initialized as ''
            json_file[name].update({
                'is_activated':True,
                'record_dt':dt
            })
            with open('/home/pi/Desktop/eds.json', 'w') as file:
                json.dump(json_file, file)
            return True
        ''' 

    def check_time(self, dt):
        # current time in minutes
        current_time = self.minute_of_day(dt)
        print(current_time)
        # declare time check
        time_check = False
        # go through the scheduled times list
        for schedule in self.schedule_time:
            # check if schedule is solar noon
            if schedule.lower() == 'sn':
                # check whether current time is within 2 min of solar noon, this will be changed based on EDS activation duration
                # since absolute, 1 min more and less
                solar_noon_min = self.get_solar_time(dt)
                if abs(solar_noon_min - current_time) < 2:
                    time_check = True
                    break
                else:
                    time_check = False
            else:
                # check whether current time is within 1 min of schedule time, this will be changed based on EDS activation duration
                if abs(int(schedule) - current_time) < 20:
                    time_check = True
                    break
                else:
                    time_check = False
        # return the time_check
        return time_check
    
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
        if self.check_leap_year(dt) == True:
            month_days = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        else:
            month_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        
        return month_days[dt.tm_mon-1] + dt.tm_mday
    
    def minute_of_day(self, dt):
        hour = dt.tm_hour
        minute = dt.tm_min
        min_day = (hour*60) + minute
        return min_day
    
    # function to calculate solar noon time in minutes
    def get_solar_time(self, dt):
        # implementation adapted from https://sciencing.com/calculate-solar-time-8612288.html
        A = 15 * self.gmt_off
        B = (dt.tm_yday - 81) * 360 / 365
        C = 9.87 * sin(deg2rad(2 * B)) - 7.53 * cos(deg2rad(B)) - 1.58 * sin(deg2rad(B))
        D = 4 * (A - self.longitude) + C
        # return solar time offset in minutes based on 12pm
        return D + 720
    
