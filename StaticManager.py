import os

'''
IMMUTABLE. DO NOT CHANGE UNLESS YOU WANT THINGS TO BREAK.
THANKS, THE MANAGEMENT
'''

# configuration file statics
CONFIG_FILE_NAME = "config.txt"
CONFIG_FILE_PATH = "" # assume local?

# data acquisition statics
V_DIVIDER_RESISTOR_GROUND = 0
V_DIVIDER_RESISTOR_BRANCH = 0

'''
DEFAULT CONFIGURATION FILE VALUES (FOR USE IN CREATING CONFIG FILE IF NONE FOUND)
NOTE: THESE ARE ONLY USED IF CONFIG FILE NOT PROVIDED
'''
# EDS default
TEST_DURATION_SECONDS = 120
EDS_TESTING_ORDER = [1,2,3,4,5,6,7,8]
IN_PIN_CURRENT_DICTIONARY = {12:"1", 16:"2", ...}
OUT_PIN_RELAY_DICTIONARY = {}
DAYS_BETWEEN_TESTING_DAYS = 0
DAILY_TESTING_TIMES = [0]
LATEST_TESTING_TIME = 5 # hours after solar noon

# testing requirements
MAX_TEMPERATURE_CELSIUS = 40
MIN_TEMPERATURE_CELSIUS = 10
MAX_RELATIVE_HUMIDITY = 50
MIN_RELATIVE_HUMIDITY = 30
AVG_SHORT_CIRCUIT_CURRENT = 0
THRESHOLD_CURRENT_RANGE = 0

# log files
LOG_FILE_NAME = "log"
DATA_FILE_NAME = "data"


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
        self.divider_res_grd = V_DIVIDER_RESISTOR_GROUND
        self.divider_res_branch = V_DIVIDER_RESISTOR_BRANCH

        self.config_dictionary = {} # sets up empty dictionary

        if self.check_for_config():
            self.load_config()
        else:
            print("Configuration file not found! Creating default file...")
            self.create_default_config()


    def check_for_config(self):
        # checks for pre-existing config file in specified directory
        return os.path.isfile(self.config_path+self.config_name)

    def create_default_config(self):
        # create default config file with parameters
        try:
            with open(self.config_name, 'w') as cfd:
                cfd.writelines("edsTestingOrder="+str(EDS_TESTING_ORDER)+'\n'
                "inPinCurrentDictionary="+str(IN_PIN_CURRENT_DICTIONARY)+'\n'
                "outPinRelayDictionary="+str(OUT_PIN_RELAY_DICTIONARY)+'\n'
                "daysBetweenTestingDays="+str(DAYS_BETWEEN_TESTING_DAYS)+'\n'
                "dailyTestingTimes="+str(DAILY_TESTING_TIMES)+'\n'
                "latestTestingTime="+str(LATEST_TESTING_TIME)+'\n'
                "maxTemperatureCelsius="+str(MAX_TEMPERATURE_CELSIUS)+'\n'
                "minTemperatureCelsius="+str(MIN_TEMPERATURE_CELSIUS)+'\n'
                "maxRelativeHumidity="+str(MAX_RELATIVE_HUMIDITY)+'\n'
                "minRelativeHumidity="+str(MIN_RELATIVE_HUMIDITY)+'\n'
                "avgShortCircuitCurrent="+str(AVG_SHORT_CIRCUIT_CURRENT)+'\n'
                "thresholdCurrentRange="+str(THRESHOLD_CURRENT_RANGE)+'\n'
                "logFileName="+LOG_FILE_NAME+'\n'
                "dataFileName="+DATA_FILE_NAME+'\n')
        except RuntimeError:
            print("Error creating default configuration file!")

    def load_config(self):
        # loads configuration file constants if file exists
        lines = []

        try:
            with open(self.config_path+self.config_name) as cf:
                lines = cf.read().split('\n')
        except RuntimeError:
            print("Error reading configuration file! Please check file.")

        # loading individual config values into config dictionary
        if lines:
            for c_string in lines:
                self.config_dictionary[c_string.split('=')[0]] = c_string.split('=')[1]
                '''
                I think this works. This is the most concise way of doing what we want here. Each dictionary key will then 
                just be the first string of each config file parameter.
                For example, self.config_dictionary['maxRelativeHumidity'] accesses the config value.
                '''
        else:
            print("Configuration file empty! Please check file.")

    def get_config(self):
        # returns config dictionary for other functions to use
        return self.config_dictionary

