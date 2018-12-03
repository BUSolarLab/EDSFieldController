import os


'''
Testing Sequence Master Class:
Functionality:
1) Verifies electrical components
2) Executes testing sequence
'''


class TestingMaster:
    
    def __init__(self, config_dictionary):
        self.okay_to_test = False
        self.param_checks = {
            'timeCheck':False,
            'celsiusCheck':False,
            'humidityCheck':False,
            'currentCheck':False
            }
        self.test_config = config_dictionary
        
        
    def time_check(self):
        # check system time against time
        return
    
    
    def temp_check(self):
        # check temperature and set flag accordingly
        min_celsius = self.test_config['minTemperatureCelsius']
        max_celsius = self.test_config['maxTemperatureCelsius']
        # get temperature data
        celsius_data = 0 # GET WEATHER SENSOR DATA HERE
        if celsius_data >= min_celsius and celsius_data <= max_celsius:
            self.param_checks['celsiusCheck'] = True
        else:
            self.param_checks['celsiusCheck'] = False
    
    
    def humidity_check(self):
        # check relative humidity and set flag accordingly
        min_humid = self.test_config['minRelativeHumidity'];
        max_humid = self.test_config['maxRelativeHumidity'];
        # get humidity data
        humid_data = 0 # GET WEATHER SENSOR DATA HERE
        if humid_data >= min_humid and humid_data <= max_humid:
            self.param_checks['humidityCheck'] = True
        else:
            self.param_checks['humidityCheck'] = False
            
    
    def current_check(self):
        # check that current values are good
        return
    

    def run_test(self):
        # checks parameter flags for okay to test before executing main test loop
        execute = True
        for key in self.param_checks:
            if not self.param_checks[key]:
                execute = False
        if not okay_to_test:
            execute = False
            
        # main test sequence
        # if execute:
        
        
        
        