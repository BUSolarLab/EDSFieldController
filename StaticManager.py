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

EDS_SCHEDULE = {
    'eds1': {
        'schedule':['SN'],
        'frequency':1
    },
    'eds2': {
        'schedule':['780'],
        'frequency':1
    },
    'eds3': {
        'schedule':['730'],
        'frequency':1
    },
    'eds4': {
        'schedule':['600'],
        'frequency':1
    },
    'eds5': {
        'schedule':['660'],
        'frequency':1
    },
}
#DO NOT CHANGE THIS UNLESS CIRCUITRY HAS CHANGED
DEFAULT_CONFIG_PARAM = {
    #EDS numbers correspond to gpio pin numbers these numbers are different than the pi pinout 
    # EDS Panels for power supply activation pin numbers
    'EDS1': 4,
    'EDS2': 17,
    'EDS3': 6,
    'EDS4': 19,
    'EDS5': 26,
    'EDS6': 27,
    # EDS and CTRL Panels measurement pin numbers
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
    'maxTemperatureCelsius': 40, #degrees C
    'minTemperatureCelsius': 10, #degrees C
    'maxRelativeHumidity': 60,   #percentage
    'minRelativeHumidity': 5,    #percentage
    'testDurationSeconds': 120, #(seconds) 2 minute, duration for EDS activation
    # indicators/switches
    #gpio pin number
    'outPinLEDGreen': 5,
    'outPinLEDRed': 13,
    'inPinManualActivate': 22,
    'manualEDSNumber': 1, #EDS 5, not pin number
    'ADC': 25,
    'solarChargerEDSNumber': 6,
    # location data for solar noon calculation
    'degLongitude': -71.05,
    'offsetGMT': -5,
    }

# dictionary for panel measurement, default panel data
PANEL_DATA = {
    'eds1':{
        'name':'EDS-PV1',
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
        'si_pre':0,
        'si_post':0,
        'frequency':EDS_SCHEDULE['eds1']['frequency'],
        'schedule':EDS_SCHEDULE['eds1']['schedule']
    },
    'eds2':{
        'name':'EDS-PV2',
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
        'si_pre':0,
        'si_post':0,
        'frequency':EDS_SCHEDULE['eds2']['frequency'],
        'schedule':EDS_SCHEDULE['eds2']['schedule']
    },
    'eds3':{
        'name':'EDS-PV3',
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
        'si_pre':0,
        'si_post':0,
        'frequency':EDS_SCHEDULE['eds3']['frequency'],
        'schedule':EDS_SCHEDULE['eds3']['schedule']
    },
    'eds4':{
        'name':'EDS-PV4',
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
        'si_pre':0,
        'si_post':0,
        'frequency':EDS_SCHEDULE['eds4']['frequency'],
        'schedule':EDS_SCHEDULE['eds4']['schedule']
    },
    'eds5':{
        'name':'EDS-PV5',
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
        'si_pre':0,
        'si_post':0,
        'frequency':EDS_SCHEDULE['eds5']['frequency'],
        'schedule':EDS_SCHEDULE['eds5']['schedule']
    },
    'ctrl1':{
        'name':'CTRL-PV1',
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
        'si_pre':0,
        'si_post':'N/A',
        'frequency':'', # No Determined Frequency
        'schedule':[] # No Determined Schedule
    },
    'ctrl2':{
        'name':'CTRL-PV2',
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
        'si_pre':0,
        'si_post':'N/A',
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

    @staticmethod
    def check_json_file(dt):
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
        #checks if json exists
        if not path.exists('/home/pi/Desktop/eds.json'):
            print("json does not exist")
            with open('/home/pi/Desktop/eds.json', 'w+') as file:
                json.dump(eds, file)
            return True
        # checks if json is blank
        elif path.getsize('/home/pi/Desktop/eds.json') <= 2:
            print(" Json file is blank ")
            with open('/home/pi/Desktop/eds.json', 'w+') as file:
                json.dump(eds, file)
            return True

        else:
            return False
    
    def check_frequency(self,name,dt):
        # check if no json file in the desktop directory
        if check_json_file(dt):
            return True
        else:
            # load the json file
            with open('/home/pi/Desktop/eds.json', 'r') as file:
                json_file = json.load(file)
            # check if it has already activated today, if it has, return true for other activation times today
            is_act = json_file[name]['is_activated']
            if is_act:
                return True
            else:
                # check for frequency confirmation, also check if it is first activation, meaning record in json will be blank
                current_day = self.day_of_year(dt)
                #Try except statement for checking if first time activation
                try:
                    activation_day = self.day_of_year(time.struct_time(tuple(json_file[name]['record_dt'])))
                except:
                    print("Firt time activation \n")
                    json_file[name].update({
                        'is_activated':True,
                        'record_dt':dt
                    })
                    with open('/home/pi/Desktop/eds.json', 'w') as file:
                        json.dump(json_file, file)
                    return True
                else:
                    print("Subsequent Activations \n")
                    # already met desired frequency for activation
                    if current_day - activation_day >= self.frequency:
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


    def check_time(self, dt):
        # current time in minutes
        current_time = self.minute_of_day(dt)
        # declare time check
        time_check = False
        # go through the scheduled times list
        for schedule in self.schedule_time:
            # check if schedule is solar noon
            if schedule.lower() == 'sn':
                # check whether current time is within 2 min of solar noon, this will be changed based on EDS activation duration
                # since absolute, 1 min more and less
                solar_noon_min = self.get_solar_time(dt)
                if abs(solar_noon_min - current_time) < 1:
                    time_check = True
                    break
                else:
                    time_check = False
            else:
                # check whether current time is within 1 min of schedule time, this will be changed based on EDS activation duration
                if abs(int(schedule) - current_time) < 1:
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
    
