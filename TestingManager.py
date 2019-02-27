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
    GPIO.output(chn, val)

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
    

    def run_test(self, eds_select, test_duration, ps_relay):
        # checks parameter flags for okay to test before executing main test loop
        '''
        execute = True
        for key in self.param_checks:
            if not self.param_checks[key]:
                execute = False
        if not okay_to_test:
            execute = False
        '''
            
        # main test sequence
        # if execute:
        #eds_relay = self.test_config[eds_select] # FOUND FROM CONFIG DICTIONARY
        
        # 1) EDS activation relays ON
        time.sleep(0.5)
        GPIO.setup(eds_relay, GPIO.OUT)
        
        time.sleep(0.5) # short delay between relay switching
        
        # 2) power supply relay ON
        GPIO.setup(ps_relay, GPIO.OUT)
        
        # 3) wait for test duration
        time.sleep(test_duration)
        
        # 4) power supply relay OFF
        GPIO.cleanup(ps_relay)
        time.sleep(0.5)
        
        # 5) EDS activation relays OFF
        GPIO.cleanup(eds_relay)
        time.sleep(0.5)
        
        
    def run_measure(self, pv_select):
        # flips relay for selected PV cell and captures short-circuit current from ADC
        pv_relay = pv_select # self.test_config[pv_select]
        print(pv_relay)
        
        # switch PV relay ON
        GPIO.setup(pv_relay, GPIO.OUT)
        time.sleep(1)
        
        read = 1 # GET READING HERE AND LOG DATA
        
        # switch PV relay OFF
        GPIO.cleanup(pv_relay)
        time.sleep(0.5)
        # DO CALCS TO GET VALUE
        return read
    
    
    def run_test_begin_manual(self, eds_select, ps_relay):
        # runs the first half of a test (pauses on test duration to allow for indefinite testing)
        
        # 1) EDS activation relays ON
        time.sleep(0.5)
        GPIO.setup(eds_select, GPIO.OUT)
        
        time.sleep(0.5) # short delay between relay switching
        
        # 2) power supply relay ON
        GPIO.setup(ps_relay, GPIO.OUT)
        
    def run_test_end_manual(self, eds_select, ps_relay):
        # runs the second half of a test to finish from first half
        # THIS MUST FOLLOW run_test_begin_manual() TO FINISH TEST PROPERLY
        # 4) power supply relay OFF
        GPIO.cleanup(ps_relay)
        time.sleep(0.5)
        
        # 5) EDS activation relays OFF
        GPIO.cleanup(eds_select)
        time.sleep(0.5)
        
