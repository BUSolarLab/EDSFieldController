import RPi.GPIO as GPIO
import time
import os
import subprocess
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# adc constants
ADC_EDS_CHAN = MCP.P0
ADC_BAT_CHAN = MCP.P1

# GPIO setup
GPIO.cleanup()

# simplified channel functions
def channel_out(chn, val):
    GPIO.output(chn, val)

def channel_in(chn):
    return GPIO.input(chn)

'''
ADC Master Class:
Functionality:
1) Initializes connection with ADC chip
2) Reads and processes raw data from ADC
3) Converts raw data into usable information
4) Logs data into .csv file
'''


class ADCMaster:
    def __init__(self):
        # create the spi bus
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

        # create the cs (chip select)
        self.cs = digitalio.DigitalInOut(board.D22)

        # create the mcp object
        self.mcp = MCP.MCP3008(self.spi, self.cs)

        # create an analog input channel on pin 0
        # GET MORE CHANNELS AS NECESSARY
        self.chan0 = AnalogIn(self.mcp, ADC_EDS_CHAN)
        self.chan1 = AnalogIn(self.mcp, ADC_BAT_CHAN)

    def get_raw_read_EDS(self):
        return self.chan0.voltage
    
    def get_raw_read_BAT(self):
        return self.chan1.voltage
    
    def process_read(self, val):
        # PROCESS RAW DATA HERE
        # might have to do some remapping from the 16-bit input
        return 1


'''
Testing Master Class:
Functionality:
1) Verifies electrical components
2) Executes testing sequence
'''


class TestingMaster:
    
    def __init__(self, config_dictionary):
        self.okay_to_test = False
        self.test_config = config_dictionary
        self.adc_m = ADCMaster()
        
        
    def get_config(self):
        return self.test_config
        
        
    # check time against schedule
    def check_time(self, dt, solar_offset, eds_num):
        sched_name = 'SCHEDS'+str(eds_num)
        schedule = self.test_config[sched_name]
        print(schedule)
        for pair in schedule:
            # if mod of the year day with schedule is zero, then day is correct
            if dt.tm_yday % pair[0] == 0:
                # convert current time to minutes and add solar time offset
                dt_min = curr.tm_hour * 60 + curr.tm_min + curr.tm_sec / 60
                dt_min_solar = curr_min + solar_offset
                
                # check if current minute is close enough to schedule time offset
                # calculate schedule time in minutes
                schedule_min = 720 + pair[1] * 60
                # if the time is within 30 seconds of scheduled time
                if abs(dt_min_solar - schedule_min) < 0.5:
                    return True
    
    # check weather against parameters
    def check_temp(self, t_curr):
        t_low = self.test_config['minTemperatureCelsius']
        t_high = self.test_config['maxTemperatureCelsius']
        # check temperature against needed conditions
        if ((1 - T_TOL) * t_low) <= t_curr <= (t_high * (1 + T_TOL)): # tolerance allows a bit outside range
            return True
        else:
            return False
        
    def check_humid(self, h_curr):
        h_low = self.test_config['minRelativeHumidity']
        h_high = self.test_config['maxRelativeHumidity']
        # check humidity against needed conditions
        if ((1 - H_TOL) * h_low) <= h_curr <= (h_high * (1 + H_TOL)): # tolerance allows a bit outside range
            return True
        else:
            return False

    

    def run_test(self, eds_select):
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
        eds_relay = self.test_config[eds_select] # FOUND FROM CONFIG DICTIONARY
        
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
        
        
    def run_measure_EDS(self):
        
        read = self.adc_m.get_raw_read_EDS()

        # LOG
        # DO CALCS TO GET VALUE
        current = read
        
        return current


    def run_measure_BAT(self, relay):
        # flips relay for battery voltage in
        GPIO.setup(relay, GPIO.OUT)
        time.sleep(1)
        
        # get reading
        read = self.adc_m.get_raw_read_BAT()
        
        # switch relay off
        GPIO.cleanup(relay)
        time.sleep(0.5)
        
        # LOG
        # DO CALCS TO GET CURRENT VALUE
        current = read
        
        return current
        
    
    def run_test_manual_begin(self, eds_select):
        # runs the first half of a test (pauses on test duration to allow for indefinite testing)
        eds_select = self.test_config['EDS'+str(eds_select)]
        ps_relay = self.test_config['POWER']
        # 1) EDS activation relays ON
        time.sleep(0.5)
        GPIO.setup(eds_select, GPIO.OUT)
        
        time.sleep(0.5) # short delay between relay switching
        
        # 2) power supply relay ON
        GPIO.setup(ps_relay, GPIO.OUT)
        
    def run_test_manual_end(self, eds_select):
        # runs the second half of a test to finish from first half
        eds_select = self.test_config['EDS'+str(eds_select)]
        ps_relay = self.test_config['POWER']
        # THIS MUST FOLLOW run_test_begin_manual() TO FINISH TEST PROPERLY
        # 4) power supply relay OFF
        GPIO.cleanup(ps_relay)
        time.sleep(0.5)
        
        # 5) EDS activation relays OFF
        GPIO.cleanup(eds_select)
        time.sleep(0.5)
        

'''
Check Functions
- these functions are used for checking parameters for initiating testing sequence
'''

def check_time(curr, solar_offset, schedule):
    for pair in schedule:
        # if mod of the year day with schedule is zero, then day is correct
        if curr.tm_yday % pair[0] == 0:
            # convert current time to minutes and add solar time offset
            curr_min = curr.tm_hour * 60 + curr.tm_min + curr.tm_sec / 60
            curr_min_solar = curr_min + solar_offset
            
            # check if current minute is close enough to schedule time offset
            # calculate schedule time in minutes
            schedule_min = 720 + pair[1] * 60
            # if the time is within 30 seconds of scheduled time
            if abs(curr_min_solar - schedule_min) < 0.5:
                print_l(curr, 'Solar time fits scheduled testing time.')
                return True
            
    
            
            
            
            


        
        
        
        
        
        
