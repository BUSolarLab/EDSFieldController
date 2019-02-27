'''
This is central control.
This file contains the main looping structure for extended-period field testing.
'''
import RPi.GPIO as GPIO
import subprocess
import time

import busio
from board import *
import adafruit_pcf8523
import AM2315

import StaticManager as SM
import DataManager as DM
import RebootManager as RM
import TestingManager as TM


# process delay (delay loop by X seconds to slow necessary computing)
PROCESS_DELAY = 1

# testing GPIO channels
OUT_CHNS = {
    'GREEN':11,
    'RED':13,
    'EDS1':18,
    'EDS2':29,
    'EDS3':31,
    'EDS4':33,
    'EDS5':35,
    'EDS6':37,
    'EDS1PV':26,
    'EDS2PV':10,
    'EDS3PV':12,
    'EDS4PV':16,
    'EDS5PV':18,
    'CTRL1PV':26,
    'CTRL2PV':28,
    'POWER':15
}

IN_CHNS = {
    'SWITCH':4,
    'ADC':24
}

# peripheral i2c bus addresses
RTC_ADD = 0x68

# read config, get constants, etc
print("Initializing...")
static_master = SM.StaticMaster()
USB_master = DM.USBMaster()
test_master = TM.TestingMaster(static_master.get_config())

# RTC setup
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)


def print_time(t):
    print(str(t.tm_mon) + '/' + str(t.tm_mday) + '/' + str(t.tm_year) + ' ' + str(t.tm_hour) + ':' + str(t.tm_min) + ':' + str(t.tm_sec), end='')

def print_l(phrase):
    print_time(rtc.datetime)
    print(" " + phrase)

# set time to current if needed
# rtc.datetime = time.struct_time((2019,2,9,16,0,0,5,40,-1))

# weather sensor setup
weather = AM2315.AM2315()


'''
~~~CORE LOOP~~~
This loop governs the overall code for the long term remote testing of the field units
1) Checks the time of day
2) Checks the temperature and humidity before testing
3) Runs testing sequence
4) Writes data to log files
5) Alerts in the case of an error
'''

# channel setups
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

'''
for channel in OUT_CHNS:
    GPIO.setup(OUT_CHNS[channel], GPIO.OUT)
    
for channel in IN_CHNS:
    GPIO.setup(IN_CHNS[channel], GPIO.IN)
'''

GPIO.setup(OUT_CHNS['GREEN'], GPIO.OUT)
GPIO.setup(IN_CHNS['SWITCH'], GPIO.IN)
GPIO.setup(OUT_CHNS['POWER'], GPIO.OUT)
GPIO.setup(OUT_CHNS['EDS1'], GPIO.OUT)
GPIO.setup(OUT_CHNS['EDS1PV'], GPIO.OUT)

# var setup
error_cycle_count = 0
flip_on = True
rtc_pass = False
temp_pass = False
humid_pass = False
schedule_pass = False

# detect switch event to manually operate EDS
GPIO.add_event_detect(IN_CHNS['SWITCH'], GPIO.RISING)

# loop indefinitely
flag = False
stopped = False
while not stopped:
    # set test pass flags false
    schedule_pass = False
    rtc_pass = False
    temp_pass = False
    humidity_pass = False
    
    # switch power supply relay OFF (make sure this is always off unless testing)
    GPIO.cleanup(OUT_CHNS['POWER'])
    
    GPIO.cleanup(OUT_CHNS['EDS1'])
    
    GPIO.cleanup(OUT_CHNS['EDS1PV'])
    
    # Check for errors (?)
    # If everything okay, flip green LED output (this will cause LED to blink 1 sec on, 1 sec off
    # If errors found, halt program and flash red LED
    
    # update time of day by getting data from RTC
    # 1) Check if RTC exists
    # 2) If yes, get time data
    
    try:
        current_time = rtc.datetime
        print_time(current_time)
        print('\n')
        
        if flip_on:
            TM.channel_out(OUT_CHNS['GREEN'], 1)
            flip_on = False
        else:
            TM.channel_out(OUT_CHNS['GREEN'], 0)
            flip_on = True
            
    except:
        print_l("ERROR. Real Time Clock not detected. Please check.")
        TM.channel_out(OUT_CHNS['RED'], 1)
        print("Waiting time: " + str(error_cycle_count) + " seconds.\n")
        
    # print current time in consol
    # print("Current time: " + RTC_get_time())
    w_read = weather.read_humidity_temperature()
    
    # check weather and print values
    print("Temp: ", w_read[1], "C")
    print("Humid: ", w_read[0], "%")

    # check time against prescribed testing times for each EDS
    # 1) If within 5 seconds of testing time for EDS, initiate testing sequence
    if 1:
        schedule_pass = True
        
    if 1:
        rtc_pass = True
        
    print(type(static_master.get_config()['maxTemperatureCelsius']))
    
    if w_read[1] < float(static_master.get_config()['maxTemperatureCelsius']) and w_read[1] > float(static_master.get_config()['minTemperatureCelsius']):
        temp_pass = True
    
    if w_read[0] < float(static_master.get_config()['maxRelativeHumidity']) and w_read[0] > float(static_master.get_config()['minRelativeHumidity']):
        humidity_pass = True
    
    #initiate testing procedure only if all flags set
    #if schedule_pass and rtc_pass and temp_pass and humidity_pass:
    if flag:
        
        print_l("Initiating testing procedure for " + "EDS1")
        # run testing procedure
        
        # 1) get control PV values for each control
        try:
            print_l("Getting Control PV data ('before').")
            pv1_data_before = test_master.run_measure('CTRL1PV')
            pv2_data_before = test_master.run_measure('CTRL2PV')
        except:
            print_l("ERROR. Cannot retrieve PV control data ('before'). Please check.")
        
        # 2) get PV 'before' value for EDS being tested
        try:
            print_l("Getting " + "EDS1" + " PV data ('before').")
            eds_data_before = test_master.run_measure('EDS1PV')
        except:
            print_l("ERROR. Cannot retrieve " + "EDS1" + " PV data ('before'). Please check.")
        
        # 3) activate EDS
        try:
            print_l("Running " + "EDS1" + " testing sequence. DO NO INTERRUPT.")
            test_master.run_test('EDS1')
        except:
            print_l("MAJOR ERROR. Cannot initiate " + "EDS1" + " testing sequence. Please check.")
        
        # 4) get PV 'after' value for EDS being tested
        try:
            print_l("Getting " + "EDS1"+ " PV data ('after').")
            eds_data_after = test_master.run_measure('EDS1PV')
        except:
            print_l("ERROR. Cannot retrieve " + "EDS1" + " PV data ('after'). Please check.")
        
        # 5) get control PV values for each control
        try:
            print_l("Getting Control PV data ('after').")
            pv1_data_after = test_master.run_measure('CTRL1PV')
            pv2_data_after = test_master.run_measure('CTRL2PV')
        except:
            print_l("ERROR. Cannot retrieve PV control data ('after'). Please check.")
            
        # finish up and give feedback
        flag = False
    
    

    
    
    
    
    if GPIO.event_detected(IN_CHNS['SWITCH']):
        # run EDS test on selected manual EDS
        
        if GPIO.input(IN_CHNS['SWITCH']):
            # flag for test duration
            man_flag = False
            
            #eds_num = static_master.get_config()['manualEDSNumber']
            eds_num = 1
            name = "EDS" + str(eds_num)
            
            # solid GREEN for duration of manual test
            TM.channel_out(OUT_CHNS['GREEN'], 1)
            print_l("FORCED. Running " + name + " testing sequence. FLIP SWITCH OFF TO STOP.")
            try:
                # measure PV current before activation
                before_cur = test_master.run_measure(OUT_CHNS['EDS1PV'])
                phrase = name + " PV [BEFORE] scC: " + str(before_cur) + " A"
                print_l(phrase)
        
                # run first half of test
                test_master.run_test_begin_manual(OUT_CHNS['EDS1'], OUT_CHNS['POWER'])
                
                # 3) wait for switch to be flipped OFF
                while not man_flag:
                    if GPIO.event_detected(IN_CHNS['SWITCH']):
                        man_flag = True
                    
                    time.sleep(0.1)
                
                # then run second half of test (cleanup phase)
                test_master.run_test_end_manual(OUT_CHNS['EDS1'], OUT_CHNS['POWER'])
                
                #test_master.run_test(name)
                after_cur = test_master.run_measure(OUT_CHNS['EDS1PV'])
                phrase = name + " PV [AFTER] scC: " + str(after_cur) + " A"
                print_l(phrase)
                
            except:
                print_l("MAJOR ERROR. Cannot initiate " + name + " testing sequence. Please check.")
        
            # either way, turn off GREEN LED indicator
            TM.channel_out(OUT_CHNS['GREEN'], 0)
    
    # delay to slow down processing
    time.sleep(PROCESS_DELAY)
    
    
    


