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
    'EDSIDS': [1, 2, 3, 4, 5],
    'CTRL1PV': 15,
    'CTRL2PV': 23,
    'CTRLIDS': [1, 2],
    # For measurement loop
    'PANELIDS':['eds1','eds2','eds3','eds4','eds5','ctrl1','ctrl2'],
    
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


'''
Panel class
Functionality:
1) Check activation/measurement frequency
2) Check with scheduled time for activation/measurement
3) Stores this information in json file in Desktop of RasPi
'''
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
    
    def check_frequency(self, mode, dt):
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