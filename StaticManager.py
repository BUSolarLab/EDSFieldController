import os
#import logfile as lgf

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
Config file parameters list (ADD NEW PARAMETERS AS DICTIONARY ENTRIES)
These also serve as default values for config file generation in event of no provided config
'''

DEFAULT_CONFIG_PARAM = {
    # EDS default testing
    'edsTestingOrder':[1,2,3,4,5,6,7,8],
    'inPinCurrentDictionary':0,
    'EDS1':27,
    'EDS2':29,
    'EDS3':31,
    'EDS4':33,
    'EDS5':35,
    'EDS6':37,
    'EDS1PV':8,
    'EDS2PV':10,
    'EDS3PV':12,
    'EDS4PV':16,
    'EDS5PV':18,
    'CTRL1PV':26,
    'CTRL2PV':28,
    'ADC':24,
    'POWER':32,
    'daysBetweenTestingDays':0,
    'dailyTestingTimes':0,
    'latestTestingTime':5, # hours after solar noon
    
    # testing requirements
    'maxTemperatureCelsius':40,
    'minTemperatureCelsius':10,
    'maxRelativeHumidity':50,
    'minRelativeHumidity':30, 
    'avgShortCircuitCurrent':0,
    'thresholdCurrentRange':0,
    
    # log files
    'logFileName':"log",
    'dataFileName':"data",
    
    # indicators/switches
    'outPinLEDGood':0,
    'outPinLEDError':0,
    'inPinManualActivate':1,
    'manualEDSNumber':1,
    
    # reboot
    'rebootFlag':False,
    'random':13,
    'random2':14,
    'random3':200
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
        self.divider_res_grd = V_DIVIDER_RESISTOR_GROUND
        self.divider_res_branch = V_DIVIDER_RESISTOR_BRANCH

        self.config_dictionary = {} # sets up empty dictionary

        if self.check_for_config():
            self.load_config()
            self.check_parameters()
        else:
            print("Configuration file not found! Creating default file...")
            #lgf.logger.warning("Config file not found, default config file generated")
            self.create_default_config()
            self.load_config()


    def check_for_config(self):
        # checks for pre-existing config file in specified directory
        return os.path.isfile(self.config_path+self.config_name)
    
    
    def create_default_config(self):
        # create default config file with parameters
        try:
            with open(self.config_name, 'w') as cfd:
                for key in DEFAULT_CONFIG_PARAM:
                    cfd.writelines(str(key)+"="+str(DEFAULT_CONFIG_PARAM[key])+'\n')
        except RuntimeError:
            print("Error creating default configuration file!")

    def load_config(self):
        # loads configuration file constants if file exists
        lines = []

        try:
            with open(self.config_path+self.config_name) as cf:
                lines = cf.read().split('\n')
        except RuntimeError:
            print("Error reading configuration file. Generating default config...")
            self.create_default_config()
            self.load_config()

        # loading individual config values into config dictionary
        if lines:
            for c_string in lines:
                if c_string != '':
                    try:
                        self.config_dictionary[c_string.split('=')[0]] = c_string.split('=')[1]
                    except:
                        print("Configuration format not correct. Generating default config...")
                        self.create_default_config()
                        self.load_config()
                        
                '''
                This is the most concise way of doing what we want here. Each dictionary key will then 
                just be the first string of each config file parameter.
                For example, self.config_dictionary['maxRelativeHumidity'] accesses the config value.
                '''
        else:
            print("Configuration file empty! Generating default config...")
            self.create_default_config()
            self.load_config()

    def check_parameters(self):
        # checks to make sure all parameters exist in self dictionary after loading from config
        for key in DEFAULT_CONFIG_PARAM:
            # if key does not exist in self dictionary, add default value to dictionary
            if key not in self.config_dictionary.keys():
                self.config_dictionary[key] = DEFAULT_CONFIG_PARAM[key]
                print("Adding parameter ["+str(key)+"] to dictionary.\n")
                # then add parameter with default value to config file (CONFIG MUST EXIST)
                with open(self.config_path+self.config_name, 'a') as cf:
                    cf_data = str(key)+"="+str(DEFAULT_CONFIG_PARAM[key])+'\n'
                    cf.write(cf_data)


    def get_config(self):
        # returns config dictionary for other functions to use
        return self.config_dictionary
    
    
    def write_reboot_flag(self, check, flag):
        # loads config file then changes reboot flag if currently false
        self.load_config()
        if self.config_dictionary["rebootFlag"] == check:
            if self.check_for_config():
                # write reboot flag as True in config file if not already true
                with open(self.config_path+self.config_name, 'r') as cf:
                    cf_data = cf.read()

                cf_data = cf_data.replace('rebootFlag='+check, 'rebootFlag='+flag)

                with open(self.config_path+self.config_name, 'w') as cf:
                    cf.write(cf_data)


