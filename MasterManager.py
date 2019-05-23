#!/usr/bin/env python3.5

'''
=============================
Title: Master Control - EDS Field Control
Author: Benjamin Considine
Started: September 2018
=============================
'''

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

from math import floor, ceil

# process delay (delay loop by X seconds to slow necessary computing)
PROCESS_DELAY = 1

# manual time test limit
MANUAL_TIME_LIMIT = 300
WINDOW_CHECK_INTERVAL = 5

# peripheral i2c bus addresses
RTC_ADD = 0x68

# read config, get constants, etc
print("Initializing...")
static_master = SM.StaticMaster()
usb_master = DM.USBMaster()
test_master = TM.TestingMaster(static_master.get_config())
print(usb_master.get_USB_path())
csv_master = DM.CSVMaster(usb_master.get_USB_path())
adc_master = TM.ADCMaster(test_master.get_pin('ADCResMain'), test_master.get_pin('ADCResOCV'), test_master.get_pin('ADCResSCC'), test_master.get_pin('ADCBatteryDiv'))

# channel setup


# RTC setup
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)


# set time to current if needed
# time struct: (year, month, month_day, hour, min, sec, week_day, year_day, is_daylightsaving?)
# run this once with the line below uncommented
# rtc.datetime = time.struct_time((2019,4,11,19,59,0,4,100,1))

# weather sensor setup
weather = AM2315.AM2315()

# set up log file
log_master = DM.LogMaster(usb_master.get_USB_path(), rtc.datetime)


# time display functions
def print_time(dt):
    print(str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec), end='')

def print_l(dt, phrase):
    print_time(dt)
    print(" " + phrase)
    log_master.write_log(dt, phrase)


# id variables for test coordination
# FIX THIS, MUST FIX CONFIG FILE STUFF (YAML or JSON FORMATS)
eds_ids = test_master.get_config()['EDSIDS']
ctrl_ids = test_master.get_config()['CTRLIDS']


# channel setups
GPIO.setmode(GPIO.BCM)

GPIO.setup(test_master.get_pin('outPinLEDGreen'), GPIO.OUT)
GPIO.setup(test_master.get_pin('outPinLEDRed'), GPIO.OUT)
GPIO.setup(test_master.get_pin('inPinManualActivate'), GPIO.IN)
GPIO.setup(test_master.get_pin('POWER'), GPIO.OUT)

# for each EDS, CTRL id, set up GPIO channel
for eds in eds_ids:
    GPIO.setup(test_master.get_pin('EDS'+str(eds)), GPIO.OUT)
    GPIO.setup(test_master.get_pin('EDS'+str(eds)+'PV'), GPIO.OUT)
    
for ctrl in ctrl_ids:
    GPIO.setup(test_master.get_pin('CTRL'+str(ctrl)+'PV'), GPIO.OUT)

# var setup
error_cycle_count = 0
flip_on = True
temp_pass = False
humid_pass = False
schedule_pass = False

# error handling
error_list = []
error_flag = False

def add_error(error):
    error_flag = True
    if error not in error_list:
        error_list.append(error)
    try:
        print_l(rtc.datetime, "ERROR FOUND: " + error)
    except:
        rtc.datetime = time.struct_time((1,1,1,1,1,1,1,1,1))
        print_l(rtc.datetime, "ERROR FOUND: " + error)

# location data for easy use in solar time calculation
gmt_offset = test_master.get_param('offsetGMT')
longitude = test_master.get_param('degLongitude')
latitude = 1 # latitude currently unused

# detect switch event to manually operate EDS
GPIO.add_event_detect(test_master.get_pin('inPinManualActivate'), GPIO.RISING)


'''
~~~CORE LOOP~~~
This loop governs the overall code for the long term remote testing of the field units
1) Checks the time of day
2) Checks the temperature and humidity before testing
3) Runs testing sequence
4) Writes data to log files
5) Alerts in the case of an error
'''


# loop indefinitely
flag = False
stopped = False

time.sleep(2)

while not stopped:
    # set all flags to False
    temp_pass = False
    humid_pass = False
    schedule_pass = False
    weather_pass = False
    
    # MASTER TRY-EXCEPT -> will still allow RED LED to blink if fatal error occurs in loop
    try:
    
        # switch power supply and EDS relays OFF (make sure this is always off unless testing)
        try:
            GPIO.setup(test_master.get_pin('POWER'),GPIO.OUT)
            GPIO.output(test_master.get_pin('POWER'), 1)
            GPIO.cleanup(test_master.get_pin('POWER'))
            for eds in eds_ids:
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds)))
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds)+'PV'))
            for ctrl in ctrl_ids:
                GPIO.cleanup(test_master.get_pin('CTRL'+str(ctrl)+'PV'))
        except:
            add_error("GPIO-Cleanup")
            
        # update time of day by getting data from RTC
        # 1) Check if RTC exists
        # 2) If yes, get time data
        print('------------------------------')
        
        # [test_ocv, test_scc] = test_master.run_measure_EDS(eds)
        # [test_ocv, test_scc] = test_master.run_measure_BAT()
        # print("OCV: ", test_ocv)
        # print("SCC: ", test_scc)
        
        # if out of loop and parameters are met
        '''
        '''
        # THE FOLLOWING IS TEST CODE FOR DEBUGGING
        if 1:
            eds = 5
            # run test if all flags passed
            print_l(rtc.datetime, "Time and weather checks passed. Initiating testing procedure for EDS" + str(eds))
            # run testing procedure
            
            curr_dt = rtc.datetime
            
            # 1) get control SCC 'before' values for each control
            ctrl_ocv_before = []
            ctrl_scc_before = []
            for ctrl in ctrl_ids:
                ocv = 0
                scc = 0
                [ocv, scc] = test_master.run_measure_CTRL(ctrl)
                ctrl_ocv_before.append(ocv)
                ctrl_scc_before.append(scc)
                print_l(rtc.datetime, "Pre-test OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_before[ctrl - 1]))
                print_l(rtc.datetime, "Pre-test SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_before[ctrl - 1]))
                            
            # 2) get SCC 'before' value for EDS being tested
            [eds_ocv_before, eds_scc_before] = test_master.run_measure_EDS(eds)
            print_l(rtc.datetime, "Pre-test OCV for EDS" + str(eds) + ": " + str(eds_ocv_before))
            print_l(rtc.datetime, "Pre-test SCC for EDS" + str(eds) + ": " + str(eds_scc_before))
            
            
            # 3) activate EDS for test duration
            
                # turn on GREEN LED for duration of test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                # run test
            test_master.run_test(eds)
                # turn off GREEN LED after test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            
            # 4) get PV 'after' value for EDS being tested
            [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds)
            print_l(rtc.datetime, "Post-test OCV for EDS" + str(eds) + ": " + str(eds_ocv_after))
            print_l(rtc.datetime, "Post-test SCC for EDS" + str(eds) + ": " + str(eds_scc_after))
            
            
            # 5) get control SCC 'after' values for each control
            ctrl_ocv_after = []
            ctrl_scc_after = []
            for ctrl in ctrl_ids:
                ocv = 0
                scc = 0
                [ocv, scc] = test_master.run_measure_CTRL(ctrl)
                ctrl_ocv_after.append(ocv)
                ctrl_scc_after.append(scc)
                print_l(rtc.datetime, "Post-test OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_after[ctrl - 1]))
                print_l(rtc.datetime, "Post-test SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_after[ctrl - 1]))
                
            # finish up, write data to CSV and give feedback
            # write data for EDS tested
            write_data = [eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after]
            # append control data
            for ctrl in ctrl_ids:
                write_data.append(ctrl_ocv_before[ctrl - 1])
                write_data.append(ctrl_ocv_after[ctrl - 1])
                write_data.append(ctrl_scc_before[ctrl - 1])
                write_data.append(ctrl_scc_after[ctrl - 1])
            
            # write data to files
            print(write_data)
            csv_master.write_testing_data(curr_dt, w_read[1], w_read[0], eds, *write_data)
        # END TEST CODE FOR DEBUGGING
        '''
        '''
        
        #try:
        #current_time = rtc.datetimebusio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        try:
            current_time = rtc.datetime
            print_time(current_time)
            print()
            solar_offset = ceil(DM.get_solar_time(gmt_offset, current_time, longitude, latitude) * 100)/100
            print('Solar offset: ', solar_offset, ' minutes')
            # remove error if corrected
            if "Sensor-RTC-1" in error_list:
                error_list.remove("Sensor-RTC-1")
        except:
            add_error("Sensor-RTC-1")
        
        # flip indicator GREEN LED to show proper working
        if flip_on:
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            flip_on = False
        else:
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            flip_on = True
        

        '''
        --------------------------------------------------------------------------
        BEGIN SOLAR NOON DATA ACQUISITION CODE
        The following code handles the automated data acquisition of SCC values for each EDS and CTRL at solar noon each day
        Code outline:
        1) Check if current time matches solar noon
        2) If yes, then for each EDS and CTRL in sequence, do the following:
            2a) Measure SCC from PV cell
            2b) Write data to CSV/text files
        3) Then activate EDS6 (the battery charger)
        '''
        
        # get current solar time
        try:
            curr_dt = rtc.datetime
            yday = TM.Y_DAYS[curr_dt.tm_mon - 1] + curr_dt.tm_mday
            # print(yday)
            solar_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60 + solar_offset
        except:
            add_error("Sensor-RTC-2")
        
        # if within 30 seconds of solar noon, run measurements
        if abs(720 - solar_time_min) < 0.5:

            print_l(rtc.datetime, "Initiating solar noon procedure for charger, EDS6")
            
            # get weather and print values in console
            try:
                w_read = weather.read_humidity_temperature()
                print("Temp: ", w_read[1], "C")
                print("Humid: ", w_read[0], "%")
                # remove error if corrected
                if "Sensor-Weather-1" in error_list:
                    error_list.remove("Sensor-Weather-1")
            except:
                add_error("Sensor-Weather-1")
            
            # EDS SCC measurements
            for eds in eds_ids:
                eds_ocv = 0
                eds_scc = 0
                [eds_ocv, eds_scc] = test_master.run_measure_EDS(eds)
                print_l(curr_dt, "Solar Noon OCV for EDS" + str(eds) + ": " + str(eds_ocv))
                print_l(curr_dt, "Solar Noon SCC for EDS" + str(eds) + ": " + str(eds_scc))
                # write data to solar noon csv/txt
                csv_master.write_noon_data(curr_dt, w_read[1], w_read[0], eds, eds_ocv, eds_scc)
            
            # CTRL SCC measurements
            for ctrl in ctrl_ids:
                ctrl_ocv = 0
                ctrl_scc = 0
                [ctrl_ocv, ctrl_scc] = test_master.run_measure_CTRL(ctrl)
                print_l(curr_dt, "Solar Noon OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv))
                print_l(curr_dt, "Solar Noon SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc))
                # write data to solar noon csv/txt
                csv_master.write_noon_data(curr_dt, w_read[1], w_read[0], -1*ctrl, ctrl_ocv, ctrl_scc)
                
            # activate EDS6 for full testing cycle (no measurements taken)
                # turn on GREEN LED for duration of test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                # run test
            test_master.run_test(test_master.get_pin('solarChargerEDSNumber'))
                # turn off GREEN LED after test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)

        '''
        END SOLAR NOON DATA ACQUISITION CODE
        --------------------------------------------------------------------------
        '''
        
        
        '''
        --------------------------------------------------------------------------
        BEGIN AUTOMATIC TESTING ACTIVATION CODE
        The following code handles the automated activation of the each EDS as specified by their schedule in config.txt
        Code outline:
        For each EDS in sequence, do the following:
        1) Check if current time matches scheduled activation time for EDS
        2) If yes, check if current weather matches testing weather parameters, within activation window
        3) If yes, run complete testing procedure for that EDS
            3a) Measure [before] SCC for control PV cells
            3b) Measure [before] SCC for EDS PV being tested
            3c) Flip relays to activate EDS for test duration
            3d) Measure [after] SCC for EDS PV being tested
            3e) Measure [after] SCC for control PV cells
            3f) Write data to CSV/txt files
        '''
        
        
        # for each EDS check time against schedule, set time flag if yes
        # put EDS in a queue if multiple are to be activated simultaneously
        eds_testing_queue = []
        
        for eds_num in eds_ids:
            # schedule_pass = test_master.check_time(rtc.datetime, solar_offset, eds_num)
            schedule_pass = test_master.check_time(curr_dt, yday, 0, eds_num)
            if schedule_pass:
                eds_testing_queue.append(eds_num)
        # print queue    
        if not not eds_testing_queue:
            phrase = "EDS Testing Queue: ["
            for eds in eds_testing_queue:
                phrase += str(eds) + " "
            phrase += "]"
            print_l(rtc.datetime, phrase)
            
        for eds in eds_testing_queue:
            # if time check is good, check temp and weather within a set window
            window = 0
            # check temp and humidity until they fall within parameter range or max window reached
            w_read = weather.read_humidity_temperature()
            
            temp_pass = test_master.check_temp(w_read[1])
            humid_pass = test_master.check_humid(w_read[0])
            weather_pass = temp_pass and humid_pass
            
            while window < test_master.get_param('testWindowSeconds') and not weather_pass:
                # increment window by 1 sec
                window += 1
                time.sleep(1)
                
                # flip GREEN LED because test not initiated yet
                if flip_on:
                    GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                    flip_on = False
                else:
                    GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
                    flip_on = True
                    
                # check temp and humidity until they fall within parameter range or max window reached
                try:
                    w_read = weather.read_humidity_temperature()
                    
                    temp_pass = test_master.check_temp(w_read[1])
                    humid_pass = test_master.check_humid(w_read[0])
                    weather_pass = temp_pass and humid_pass
                    
                    # remove error if corrected
                    if "Sensor-Weather-2" in error_list:
                        error_list.remove("Sensor-Weather-2")
                except:
                    add_error("Sensor-Weather-2")
            
            # if out of loop and parameters are met
            if weather_pass:
                # run test if all flags passed
                print_l(rtc.datetime, "Time and weather checks passed. Initiating testing procedure for EDS" + str(eds))
                # run testing procedure
                
                curr_dt = rtc.datetime
                
                # 1) get control SCC 'before' values for each control
                ctrl_ocv_before = []
                ctrl_scc_before = []
                for ctrl in ctrl_ids:
                    ocv = 0
                    scc = 0
                    [ocv, scc] = test_master.run_measure_CTRL(ctrl)
                    ctrl_ocv_before.append(ocv)
                    ctrl_scc_before.append(scc)
                    print_l(rtc.datetime, "Pre-test OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_before[ctrl - 1]))
                    print_l(rtc.datetime, "Pre-test SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_before[ctrl - 1]))
                                
                # 2) get SCC 'before' value for EDS being tested
                [eds_ocv_before, eds_scc_before] = test_master.run_measure_EDS(eds)
                print_l(rtc.datetime, "Pre-test OCV for EDS" + str(eds) + ": " + str(eds_ocv_before))
                print_l(rtc.datetime, "Pre-test SCC for EDS" + str(eds) + ": " + str(eds_scc_before))
                
                
                # 3) activate EDS for test duration
                
                    # turn on GREEN LED for duration of test
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                    # run test
                test_master.run_test(eds)
                    # turn off GREEN LED after test
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
                
                # 4) get PV 'after' value for EDS being tested
                [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds)
                print_l(rtc.datetime, "Post-test OCV for EDS" + str(eds) + ": " + str(eds_ocv_after))
                print_l(rtc.datetime, "Post-test SCC for EDS" + str(eds) + ": " + str(eds_scc_after))
                
                
                # 5) get control SCC 'after' values for each control
                ctrl_ocv_after = []
                ctrl_scc_after = []
                for ctrl in ctrl_ids:
                    ocv = 0
                    scc = 0
                    [ocv, scc] = test_master.run_measure_CTRL(ctrl)
                    print_l(rtc.datetime, "Post-test OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_after[ctrl - 1]))
                    print_l(rtc.datetime, "Post-test SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_after[ctrl - 1]))
                    
                # finish up, write data to CSV and give feedback
                # write data for EDS tested
                write_data = [eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after]
                # append control data
                for ctrl in ctrl_ids:
                    write_data.append(ctrl_ocv_before[ctrl - 1])
                    write_data.append(ctrl_ocv_after[ctrl - 1])
                    write_data.append(ctrl_scc_before[ctrl - 1])
                    write_data.append(ctrl_scc_after[ctrl - 1])
                
                # write data to files
                csv_master.write_testing_data(curr_dt, w_read[1], w_read[0], eds, write_data)
                
                print_l(rtc.datetime, "Ended automated scheduled test of EDS" + str(eds))
                
        '''
        END AUTOMATIC TESTING ACTIVATION CODE
        --------------------------------------------------------------------------
        '''

        
        '''
        --------------------------------------------------------------------------
        BEGIN MANUAL ACTIVATION CODE
        The following code handles the manual activation of the specified EDS (in config.txt) by flipping the switch
        Code outline:
        1) Check for changing input on switch pin
        2) If input is changed, and input is high (activate), then begin test
        3) Check SCC on EDS for [before] measurement
        4) Run first half of test, but loop until switched off or max time elapsed
        5) Run second half of test
        6) Check SCC on EDS for [after] measurement
        '''
        
        if GPIO.event_detected(test_master.get_pin('inPinManualActivate')):
            # run EDS test on selected manual EDS
            
            if GPIO.input(test_master.get_pin('inPinManualActivate')):
                # flag for test duration
                man_flag = False
                
                eds_num = test_master.get_pin('manualEDSNumber')
                
                # get weather and time for data logging
                curr_dt = rtc.datetime
                w_read = weather.read_humidity_temperature()
                
                # solid GREEN for duration of manual test
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                print_l(rtc.datetime, "FORCED. Running EDS" + str(eds_num) + " testing sequence. FLIP SWITCH OFF TO STOP.")
                try:
                    # measure PV current before activation
                    [eds_ocv_before, eds_scc_before] = test_master.run_measure_EDS(eds_num)
                    print_l(rtc.datetime, "Pre-test OCV for EDS" + str(eds_num) + ": " + str(eds_ocv_before)) 
                    print_l(rtc.datetime, "Pre-test SCC for EDS" + str(eds_num) + ": " + str(eds_scc_before))            
            
                    # run first half of test
                    test_master.run_test_begin(eds_num)
                    time_elapsed = 0
                    
                    # 3) wait for switch to be flipped OFF
                    while not man_flag:
                        if GPIO.event_detected(test_master.get_pin('inPinManualActivate')):
                            man_flag = True
                            
                        time_elapsed += 0.1
                        if time_elapsed > MANUAL_TIME_LIMIT:
                            man_flag = True
                        
                        time.sleep(0.1)
                    
                    # then run second half of test (cleanup phase)
                    test_master.run_test_end(eds_num)
                    
                    [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds_num)
                    print_l(rtc.datetime, "Post-test SCC for EDS" + str(eds_num) + ": " + str(eds_ocv_after))
                    print_l(rtc.datetime, "Post-test SCC for EDS" + str(eds_num) + ": " + str(eds_scc_after))
                    
                    # write data for EDS tested
                    csv_master.write_testing_data(curr_dt, w_read[1], w_read[0], eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after)
                    
                    print_l(rtc.datetime, "Ended manual test of EDS" + str(eds_num))
                
                except:
                    print_l(rtc.datetime, "Error with manual testing sequence. Please check.")
                    add_error("Test-Manual")
            
            
                # either way, turn off GREEN LED indicator
                GPIO.output(test_master.get_pin('outPinLEDGreen'),0)
        
        '''
        END MANUAL ACTIVATION CODE
        --------------------------------------------------------------------------
        '''
        
        # remove error if corrected
        if "FATAL CORE ERROR" in error_list:
            error_list.remove("FATAL CORE ERROR")
    
    # END MASTER TRY-EXCEPT envelope
    except:
        add_error("FATAL CORE ERROR")
        raise
        
    
    if not not error_list:
        e_phrase = "Current error list: "
        for err in error_list:
            e_phrase += " [" + err + "]"
        print_l(rtc.datetime, e_phrase)
        
    # flip indicator RED LED if error flag raised
    if error_flag:
        if flip_on:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
        else:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0) 
    
    
    # delay to slow down processing
    time.sleep(PROCESS_DELAY)
    
    # END CORE LOOP
    


