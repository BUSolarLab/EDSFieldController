'''
=============================
Title: Configuration File Management - EDS Field Control
Author: Benjamin Considine
Started: September 2018
=============================
'''

import os
import json

'''
IMMUTABLE. DO NOT CHANGE UNLESS YOU WANT THINGS TO BREAK.
THANKS, THE MANAGEMENT
'''

# configuration file statics
CONFIG_FILE_NAME = "config.json"
CONFIG_FILE_PATH = "/home/pi/EDSPython/" # assume local?


'''
Config file parameters list (ADD NEW PARAMETERS AS DICTIONARY ENTRIES)
These also serve as default values for config file generation in event of no provided config
'''

DEFAULT_CONFIG_PARAM = {
    # EDS default testing
    'SCHEDS1':[[1,-3],[1,-2],[1,-1]],
    'SCHEDS2':[[1,-3],[1,-2]],
    'SCHEDS3':[[1,-2]],
    'SCHEDS4':[[2,-2]],
    'SCHEDS5':[[3,-2]],
    'SCHEDS6':[[1,0]],
    'EDS1':4,
    'EDS2':17,
    'EDS3':6,
    'EDS4':19,
    'EDS5':26,
    'EDS6':27,
    'EDS1PV':14,
    'EDS2PV':18,
    'EDS3PV':12,
    'EDS4PV':16,
    'EDS5PV':20,
    'EDSIDS':[1,2,3,4,5],
    'CTRL1PV':15,
    'CTRL2PV':23,
    'CTRLIDS':[1,2],
    'POWER':24,
    'OCVBRANCH':25,
    'SCCBRANCH':7,
    
    # testing requirements
    'maxTemperatureCelsius':40,
    'minTemperatureCelsius':10,
    'maxRelativeHumidity':60,
    'minRelativeHumidity':30,
    'testDurationSeconds':120,
    'testWindowSeconds':2700,
    'ADCResMain':68000,
    'ADCResOCV':10000,
    'ADCResSCC':1,
    'ADCBatteryDiv':10,
    
    # indicators/switches
    'outPinLEDGreen':5,
    'outPinLEDRed':13,
    'inPinManualActivate':22,
    'manualEDSNumber':1,
    'solarChargerEDSNumber':6,
    
    # reboot
    'rebootFlag':False,
    
    # location data
    'degLongitude':-71.05,
    'offsetGMT':-4,
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
        self.config_name = CONFIG_FILE_NAME
        self.config_path = CONFIG_FILE_PATH
        
        self.config_dictionary = {} # set up empty dictionary
        
        if self.check_for_config():
            self.load_config()
            self.check_parameters()
        else:
            print("Configuration file not found! Creating default file...")
            self.create_default_config()
            self.load_config()
            
    
    def check_for_config(self):
        # checks for pre-existing config file in specified directory
        return os.path.isfile(self.config_path+self.config_name)
    
    
    def create_default_config(self):
        # create config file with default parameters
        with open(self.config_path+self.config_name, 'w') as cf:
            json.dump(DEFAULT_CONFIG_PARAM, cf)
            
            
    def load_config(self):
        # load config file if already exists
        try:
            with open(self.config_path+self.config_name, 'r') as cf:
                self.config_dictionary = json.load(cf)
                print("Loaded .json file successfully.")
        except:
            # remove faulty file if it can't be loaded
            print("Error loading configuration file. Deleting and remaking with default parameters!")
            if os.path.isfile(self.config_path+self.config_name):
                os.remove(self.config_path+self.config_name)
            # create default file after deleting corrupted file
            self.create_default_config()
            
            
    def check_parameters(self):
        # checks to make sure all parameters exist in self dictionary after loading from config
        for key in DEFAULT_CONFIG_PARAM:
            # if key does not exist in self dictionary, add default value to dictionary
            if key not in self.config_dictionary.keys():
                self.config_dictionary[key] = DEFAULT_CONFIG_PARAM[key]
                print("Adding parameter ["+str(key)+"] to dictionary.\n")
                # then add parameter with default value to config file (CONFIG MUST EXIST)
                with open(self.config_path+self.config_name, 'w') as cf:
                    json.dump(self.config_dictionary, cf)
                    
                    
    def get_config(self):
        # returns config dictionary for other functions to use
        return self.config_dictionary


