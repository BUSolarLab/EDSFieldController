'''
=============================
Title: Testing and Data Collection - EDS Field Control
Author: Benjamin Considine
Started: September 2018
=============================
'''

import RPi.GPIO as GPIO
import time
import os
import subprocess
import busio
import digitalio
import board
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
# import adafruit_mcp3xxx.mcp3008 as MCP
# from adafruit_mcp3xxx.analog_in import AnalogIn

# adc constants
ADC_PV_CHAN = 1
ADC_BAT_CHAN = 2
SPI_PORT   = 0
SPI_DEVICE = 0
VREF = 3.3
STEPS = 1023

# year days for start of each month (because the clock doesn't want to keep tm_yday for some reason)
# don't care about leap year
Y_DAYS = [0,31,59,90,120,151,181,212,243,273,304,334]

# tolerances for humidity and temperature scheduling
T_TOL = 0.1
H_TOL = 0.1
MIN_CHECK_THRESHOLD = 0.5

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
    def __init__(self, r1, r2, r3, bdiv):
        # using hardware SPI
        self.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
        # circuit resistor values
        self.main_res = r1
        self.ocv_res = r2
        self.scc_res = r3
        self.bat_div = bdiv
        
    def get_ocv_PV(self, chan):
        raw = self.mcp.read_adc(chan)
        print('PV raw volt read: ', raw)
        # voltage divider multiplier
        vdiv = self.main_res / self.ocv_res
        # get percent of vref, then multiply by vdiv for actual volts
        return vdiv * VREF * raw / STEPS
    
    def get_scc_PV(self, chan):
        raw = self.mcp.read_adc(chan)
        print('PV raw curr read: ', raw)
        # approximate SCC because scc_res << main_res
        return raw * VREF / STEPS / self.scc_res
    
    def get_ocv_BAT(self, chan):
        raw = self.mcp.read_adc(chan)
        print('Battery raw volt read: ', raw)
        # voltage divider calc
        return self.bat_div * VREF * raw / STEPS        


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
        self.adc_m = ADCMaster(self.test_config['ADCResMain'], self.test_config['ADCResOCV'], self.test_config['ADCResSCC'], self.test_config['ADCBatteryDiv'])
        
    # simple getter for config dictionary
    def get_config(self):
        return self.test_config
    
    # gets a float type value for dictionary entry (will need this a lot)
    def get_param(self, key):
        return float(self.test_config[key])
    
    # get int type from dicationary if GPIO pin value needed
    def get_pin(self, key):
        return int(self.test_config[key])
        
        
    # check time against schedule
    def check_time(self, dt, yday, solar_offset, eds_num):
        sched_name = 'SCHEDS'+str(eds_num)
        schedule = self.test_config[sched_name]
        for pair in schedule:
            # if mod of the year day with schedule is zero, then day is correct
            if yday % float(pair[0]) == 0:
                # convert current time to minutes and add solar time offset
                dt_min = dt.tm_hour * 60 + dt.tm_min + dt.tm_sec / 60
                dt_min_solar = dt_min + solar_offset
                
                # check if current minute is close enough to schedule time offset
                # calculate schedule time in minutes
                schedule_min = 720 + float(pair[1]) * 60
                # if the time is within 30 seconds of scheduled time
                if abs(dt_min_solar - schedule_min) < MIN_CHECK_THRESHOLD:
                    return True
    
    # check weather against parameters
    def check_temp(self, t_curr):
        t_low = self.get_param('minTemperatureCelsius')
        t_high = self.get_param('maxTemperatureCelsius')
        # check temperature against needed conditions
        if ((1 - T_TOL) * t_low) <= t_curr <= (t_high * (1 + T_TOL)): # tolerance allows a bit outside range
            return True
        else:
            print("Temperature (", t_curr, " C) not within testing parameters. Will check again shortly.")
            return False
        
    def check_humid(self, h_curr):
        h_low = self.get_param('minRelativeHumidity')
        h_high = self.get_param('maxRelativeHumidity')
        # check humidity against needed conditions
        if ((1 - H_TOL) * h_low) <= h_curr <= (h_high * (1 + H_TOL)): # tolerance allows a bit outside range
            return True
        else:
            print("Humidity (", h_curr, " %) not within testing parameters. Will check again shortly.")
            return False

    
    # main test sequence
    def run_test(self, eds_num):
        #  main test sequence to be run after checking flags in MasterManager
        test_duration = self.get_param('testDurationSeconds')
        # run first half of test
        self.run_test_begin(eds_num)
        # wait for test duration
        time.sleep(test_duration)
        # run second half of test
        self.run_test_end(eds_num)
        
    def run_measure_EDS(self, eds_num):
        # get pin for PV relay
        pv_relay = self.get_pin('EDS' + str(eds_num) + 'PV')
        ocv_trans = self.get_pin('OCVBRANCH')
        scc_trans = self.get_pin('SCCBRANCH')
        
        # flip EDS pv relay to measure SCC
        time.sleep(0.5)
        GPIO.setup(pv_relay, GPIO.OUT)
        time.sleep(0.5)
        
        # OCV READ
        # switch transistor to draw through branch
        GPIO.setup(ocv_trans, GPIO.OUT)
        GPIO.output(ocv_trans, 1)
        time.sleep(0.5)
        # get reading
        read_ocv = self.adc_m.get_ocv_PV(ADC_PV_CHAN)
        # switch transistor back
        time.sleep(0.25)
        GPIO.output(ocv_trans, 0)
        GPIO.cleanup(ocv_trans)
        
        # SCC READ
        # switch transistor to draw through branch
        GPIO.setup(scc_trans, GPIO.OUT)
        GPIO.output(scc_trans, 1)
        time.sleep(0.5)
        # get reading
        read_scc = self.adc_m.get_scc_PV(ADC_PV_CHAN)
        # switch transistor back
        time.sleep(0.25)
        GPIO.output(scc_trans, 0)
        GPIO.cleanup(scc_trans)
        
        # close EDS pv relay
        time.sleep(0.5)
        GPIO.cleanup(pv_relay)
        time.sleep(0.5)
        
        return [read_ocv, read_scc]
    
    
    def run_measure_CTRL(self, ctrl_num):
        # get pin for PV relay
        pv_relay = self.get_pin('CTRL' + str(ctrl_num) + 'PV')
        ocv_trans = self.get_pin('OCVBRANCH')
        scc_trans = self.get_pin('SCCBRANCH')
        
        # flip EDS pv relay to measure SCC
        time.sleep(0.5)
        GPIO.setup(pv_relay, GPIO.OUT)
        time.sleep(0.5)
        
        # OCV READ
        # switch transistor to draw through branch
        GPIO.setup(ocv_trans, GPIO.OUT)
        GPIO.output(ocv_trans, 1)
        time.sleep(0.5)
        # get reading
        read_ocv = self.adc_m.get_ocv_PV(ADC_PV_CHAN)
        # switch transistor back
        time.sleep(0.25)
        GPIO.output(ocv_trans, 0)
        GPIO.cleanup(ocv_trans)
        
        # SCC READ
        # switch transistor to draw through branch
        GPIO.setup(scc_trans, GPIO.OUT)
        GPIO.output(scc_trans, 1)
        time.sleep(0.5)
        # get reading
        read_scc = self.adc_m.get_scc_PV(ADC_PV_CHAN)
        # switch transistor back
        time.sleep(0.25)
        GPIO.output(scc_trans, 0)
        GPIO.cleanup(scc_trans)
        
        # close EDS pv relay
        time.sleep(0.5)
        GPIO.cleanup(pv_relay)
        time.sleep(0.5)
        
        return [read_ocv, read_scc]


    def run_measure_BAT(self):
        # the battery will not require flipping relays/transistors (only ~14uW power lost)
        
        # get reading
        read_ocv = self.adc_m.get_ocv_BAT(ADC_BAT_CHAN)
        
        return read_ocv
        
    
    def run_test_begin(self, eds_num):
        # runs the first half of a test (pauses on test duration to allow for indefinite testing)
        eds_select = self.get_pin('EDS'+str(eds_num))
        ps_relay = self.get_pin('POWER')
        # 1) EDS activation relays ON
        time.sleep(0.5)
        GPIO.setup(eds_select, GPIO.OUT)
        time.sleep(0.5) # short delay between relay switching
        # 2) power supply relay ON
        GPIO.setup(ps_relay, GPIO.OUT)
        GPIO.output(ps_relay, 1)
        
    def run_test_end(self, eds_num):
        # runs the second half of a test to finish from first half
        eds_select = self.get_pin('EDS'+str(eds_num))
        ps_relay = self.get_pin('POWER')
        # THIS MUST FOLLOW run_test_begin() TO FINISH TEST PROPERLY
        # 4) power supply relay OFF
        GPIO.output(ps_relay, 0)
        GPIO.cleanup(ps_relay)
        time.sleep(0.5)
        # 5) EDS activation relays OFF
        GPIO.cleanup(eds_select)
        time.sleep(0.5)
        


        
