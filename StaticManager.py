'''
=============================
Title: Configuration File Management - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''

'''
Config file parameters list (ADD NEW PARAMETERS AS DICTIONARY ENTRIES)
'''

DEFAULT_CONFIG_PARAM = {
    # EDS default testing
    'EDS1': 4,
    'EDS2': 17,
    'EDS3': 6,
    'EDS4': 19,
    'EDS5': 26,
    'EDS6': 27,
    'EDS1PV': 7,
    'EDS2PV': 8,
    'EDS3PV': 12,
    'EDS4PV': 16,
    'EDS5PV': 20,
    'EDS6PV': 21,
    'EDSIDS': [1, 2, 3, 4, 5],
    'CTRL1PV': 15,
    'CTRL2PV': 23,
    'CTRLIDS': [1, 2],
    'PANELIDS':['eds1','eds2','eds3','eds4','eds5','ctrl1','ctrl2'],
    
    # testing requirements
    'maxTemperatureCelsius': 40,
    'minTemperatureCelsius': 10,
    'maxRelativeHumidity': 60,
    'minRelativeHumidity': 20,
    'testDurationSeconds': 60, # 1 minute
    'testWindowSeconds': 2700,
    
    # indicators/switches
    'outPinLEDGreen': 5,
    'outPinLEDRed': 13,
    'inPinManualActivate': 22,
    'manualEDSNumber': 5, #EDS 3
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
        'sr_post':0
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
        'sr_post':0
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
        'sr_post':0
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
        'sr_post':0
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
        'sr_post':0
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
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0
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
        'ocv_post':0,
        'scc_pre':0,
        'scc_post':0,
        'pwr_pre':0,
        'pwr_post':0,
        'pr_pre':0,
        'pr_post':0,
        'sr_pre':0,
        'sr_post':0
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