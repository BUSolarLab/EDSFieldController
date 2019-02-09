import os
import RPi.GPIO as GPIO
import time

'''
Testing Sequence Master Class:
Functionality:
1) Verifies electrical components
2) Executes testing sequence
'''

# GPIO setup
GPIO.cleanup()

# simplified channel functions
def channel_out(chn, val):
    print('here')
    GPIO.output(chn, val)
    print('here2')

def channel_in(chn):
    return GPIO.input(chn)


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
    

    def run_test(self, eds_select):
        # checks parameter flags for okay to test before executing main test loop
        execute = True
        for key in self.param_checks:
            if not self.param_checks[key]:
                execute = False
        if not okay_to_test:
            execute = False
            
        # main test sequence
        # if execute:
        eds_relay = self.test_config[eds_select] # FOUND FROM CONFIG DICTIONARY
        ps_relay = 32 # FOUND FROM CONFIG DICTIONARY
        test_duration = 5 # FOUND FROM CONFIG DICTIONARY
        
        # 1) EDS activation relays ON
        time.sleep(0.5)
        channel_out(eds_relay, 1)
        time.sleep(0.5) # short delay between relay switching
        
        # 2) power supply relay ON
        channel_out(ps_relay, 1)
        
        # 3) wait for test duration
        time.sleep(test_duration)
        
        # 4) power supply relay OFF
        channel_out(ps_relay, 0)
        time.sleep(0.5)
        
        # 5) EDS activation relays OFF
        channel_out(eds_relay, 0)
        time.sleep(0.5)
        
        
    def run_measure(self, pv_select):
        # flips relay for selected PV cell and captures short-circuit current from ADC
        pv_relay = self.test_config[pv_select]
        print(pv_relay)
        
        # switch PV relay ON
        channel_out(pv_relay, 1)
        time.sleep(0.5)
        
        read = 1 # GET READING HERE
        
        # switch PV relay OFF
        channel_out(pv_relay, 0)
        time.sleep(0.5)
        # DO CALCS TO GET VALUE
        return read
        
        
        
        
        
        
