'''
=============================
Title: Testing and Data Collection - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''

import RPi.GPIO as GPIO
import time
import math
import os
import subprocess
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP 
from adafruit_mcp3xxx.analog_in import AnalogIn

# year days for start of each month (because the clock doesn't want to keep tm_yday for some reason)
# don't care about leap year
Y_DAYS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

# tolerances for humidity and temperature scheduling
T_TOL = 0.1
H_TOL = 0.1

# how close current time must be to scheduled time to initiate test (min)
MIN_CHECK_THRESHOLD = 0.5

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
        #GPIO pin to trigger the relay, high is OCV, low is SCC
        GPIO.setup(25, GPIO.OUT)
        #Properties
        self.bat_div = 10
        
    def get_ocv_PV(self):
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D18)
        mcp = MCP.MCP3008(spi, cs)
        chan=AnalogIn(mcp, MCP.P0)
        raw = chan.voltage
        print('PV Raw volt read: ' + str(raw) + '[V]')
        # Since we divided voltage by 11, multiply by 11 to get actual Voc
        return raw * 11
    
    def get_scc_PV(self):
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D18)
        mcp = MCP.MCP3008(spi, cs)
        chan=AnalogIn(mcp, MCP.P0)
        raw = chan.voltage
        print('PV Raw curr read: ' + str(raw) + '[A]')
        #SCC = Voc x 1 ohm
        return raw
    
    def get_ocv_BAT(self):
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D18)
        mcp = MCP.MCP3008(spi, cs)
        chan=AnalogIn(mcp, MCP.P0)
        raw = self.mcp.read_adc(chan)
        print('Battery raw volt read: ' + str(raw) + '[V]')
        # voltage divider calc
        return self.bat_div * 3.3 * raw / 1023

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

    # Activating all EDS panels during noon time
    def activate_eds(self, eds_ids):
        #  main test sequence to be run after checking flags in MasterManager
        eds_duration = self.get_param('testDurationSeconds')
        # run first half of activation for all EDS panels
        for eds_num in eds_ids:
            self.run_test_begin(eds_num)
        # wait for EDS to activate
        time.sleep(eds_duration)
        # run second half to turn off EDS
        for eds_num in eds_ids:
            self.run_test_end(eds_num)

    # Activating EDS to repel soiling/dust/etc
    def run_test(self, eds_num):
        #  main test sequence to be run after checking flags in MasterManager
        test_duration = self.get_param('testDurationSeconds')
        # run first half of test
        self.run_test_begin(eds_num)
        # wait for test duration
        time.sleep(test_duration)
        # run second half of test
        self.run_test_end(eds_num)

    # Measure Voc and Isc of EDS
    def run_measure_EDS(self, eds_num):
        # Get pin for PV relay
        pv_relay = self.get_pin('EDS' + str(eds_num) + 'PV')
        
        # Setup GPIO pins to measure Voc and Isc of desired panel
        time.sleep(0.5)
        GPIO.setup(pv_relay, GPIO.OUT)
        GPIO.setup(25,GPIO.OUT)
        time.sleep(0.5)
        
        # OCV READ
        # Switch the relay to read Voc
        GPIO.setup(25, GPIO.IN)
        time.sleep(0.5)
        # Get reading
        read_ocv = self.adc_m.get_ocv_PV()
        
        # SCC READ
        # Switch relay to read Isc
        GPIO.setup(25, GPIO.OUT)
        time.sleep(0.5)
        # get reading
        read_scc = self.adc_m.get_scc_PV()

        # Default pin is LOW, no need to switch, just clean up
        time.sleep(0.5)
        GPIO.cleanup(25)
        
        # Close EDS PV Relay
        time.sleep(0.5)
        GPIO.cleanup(pv_relay)
        time.sleep(0.5)
        
        return [read_ocv, read_scc]
    
    
    def run_measure_CTRL(self, ctrl_num):
        # Get pin for PV relay
        pv_relay = self.get_pin('CTRL' + str(ctrl_num) + 'PV')
        
        # Setup GPIO pins to measure Voc and Isc of desired panel
        time.sleep(0.5)
        GPIO.setup(pv_relay, GPIO.OUT)
        GPIO.setup(25,GPIO.OUT)
        time.sleep(0.5)
        
        # OCV READ
        # Switch the relay to read Voc
        GPIO.setup(25, GPIO.IN)
        time.sleep(0.5)
        # Get reading
        read_ocv = self.adc_m.get_ocv_PV()
        
        # SCC READ
        # Switch relay to read Isc
        GPIO.setup(25, GPIO.OUT)
        time.sleep(0.5)
        # get reading
        read_scc = self.adc_m.get_scc_PV()
        # Default pin is LOW, no need to switch, just clean up
        time.sleep(0.5)
        GPIO.cleanup(25)
        
        # Close EDS PV Relay
        time.sleep(0.5)
        GPIO.cleanup(pv_relay)
        time.sleep(0.5)
        
        return [read_ocv, read_scc]


    def run_measure_BAT(self):
        # the battery will not require flipping relays/transistors (only ~14uW power lost)
        # get reading
        read_ocv = self.adc_m.get_ocv_BAT()
        return read_ocv
        
    
    def run_test_begin(self, eds_num):
        # runs the first half of a test (pauses on test duration to allow for indefinite testing)
        eds_select = self.get_pin('EDS'+str(eds_num))

        # EDS activation relays ON
        GPIO.setup(eds_select, GPIO.OUT)
        GPIO.output(eds_select, GPIO.HIGH)
        # short delay between relay switching
        time.sleep(0.5)

        
    def run_test_end(self, eds_num):
        # runs the second half of a test to finish from first half
        eds_select = self.get_pin('EDS'+str(eds_num))

        # THIS MUST FOLLOW run_test_begin() TO FINISH TEST PROPERLY
        # deactivate the EDS
        GPIO.output(eds_select, GPIO.LOW)
        GPIO.cleanup(eds_select)
        time.sleep(0.5)

'''
Power Master Class:
Functionality:
1) Takes in voc, isc, and temperature as inputs
2) Measures power output
'''
class PowerMaster:
    def __init__(self):
        #Solar Panel Specifications
        self.v_mp = 17 #Operating voltage/max point voltage
        self.i_mp = 0.58 #Operating current/max point current
        self.v_nom = 12 #Nominal voltage
        self.p_max = 10 #Max Power
        self.voc = 21.5 #Open Circuit Voltage
        self.isc = 0.68 #Short Circuit Current

        #Readings from sensors defaults to -1
        self.v_oc = -1
        self.i_sc = -1
        self.temp = -1

    def get_power_out(self,v_oc,i_sc,temp):
        #Get normalized open circuit voltage
        v_norm = self.voltage_normalized(v_oc, temp)
        #Compute the fill factor
        FF = self.fill_factor(v_norm)
        #Calculate the output power
        p_out = v_oc * i_sc * FF
        return p_out
    
    def fill_factor(self,v_norm):
        #Compute fill factor using normalized voltage
        FF = (v_norm - math.log(v_norm+0.72))/(v_norm+1)
        return FF

    def voltage_normalized(self,v_oc,temp):
        #Coulomb constant
        q = 1.6*10**-19
        #Ideality factor, 1 for Si
        n = 1
        #Boltzmann Constant
        k = 1.38*10**-23
        #Calculate normalized temperature
        cells = 36 #number of cells in the solar panel
        v_norm = (v_oc/cells) * (q/(n*k*temp))
        return v_norm
    
    def get_panel_temp(self,amb_temp, g_poa):
        noct = 47 #This needs to be confirmed
        t_pan = amb_temp + ((noct - 20)*g_poa)/800
        return t_pan

'''
Performance Ratio Class:
Functionality:
1) Takes in voc, isc, and temperature as inputs
2) Measures power output
'''

class PerformanceRatio:
    def __init__(self):
        #Summation of installed module's namemplate rating, for field testing just 1 panel so 12W
        self.ptc = 12
        #Irradiance at STC
        self.gstc = 1000

    def get_pr(self,v_oc,i_sc,temp, power, gpoa):
        if (gpoa == 0):
            PR = -1
        elif (gpoa == -1):
            PR = -1
        else:
            PR = power/((self.ptc*gpoa)/self.gstc)
        return round(PR,2)

'''
Soiling Class:
Functionality:
1) Takes in isc before and isc after
2) Measures soiling ratio
'''
class Soiling:
    def __init__(self):
        #Nameplate rating of isc, representing isc_clean
        self.isc_clean = 0.68
        #Irradiance at STC
        self.gstc = 1000

    #Soiling Ratio Formula
    def get_sr(self,isc_soiled):
        SR = isc_soiled/self.isc_clean
        return round(SR,2)