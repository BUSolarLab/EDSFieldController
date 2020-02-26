'''
=============================
Title: Master Control - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''

# dependencies
import RPi.GPIO as GPIO
import subprocess
import time
import busio
from board import *
import adafruit_pcf8523
import AM2315
import SP420
import StaticManager as SM
import DataManager as DM
import TestingManager as TM
from math import floor, ceil

# read config, get constants, etc
print("Initializing...")
static_master = SM.StaticMaster()
usb_master = DM.USBMaster()
test_master = TM.TestingMaster(static_master.get_config())
print(usb_master.get_USB_path())
csv_master = DM.CSVMaster(usb_master.get_USB_path())
adc_master = TM.ADCMaster()
pow_master = TM.PowerMaster()
pr_master = TM.PerformanceRatio()
soil_master = TM.Soiling()

# weather sensor setup
weather = AM2315.AM2315()

# RTC setup
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

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
eds_ids = test_master.get_config()['EDSIDS']
ctrl_ids = test_master.get_config()['CTRLIDS']
panel_ids = test_master.get_config()['PANELIDS']
panel_data = static_master.get_panel_data()

# channel setups
GPIO.setmode(GPIO.BCM)

# LED port setup
GPIO.setup(test_master.get_pin('outPinLEDGreen'), GPIO.OUT)
GPIO.setup(test_master.get_pin('outPinLEDRed'), GPIO.OUT)

# manual button port setup
GPIO.setup(test_master.get_pin('inPinManualActivate'), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(test_master.get_pin('inPinManualActivate'), GPIO.RISING)

# adc chip port setup
GPIO.setup(test_master.get_pin('ADC'), GPIO.OUT)

# for each EDS, CTRL id, set up GPIO channel
for eds in eds_ids:
    GPIO.setup(test_master.get_pin('EDS'+str(eds)), GPIO.OUT)
    GPIO.setup(test_master.get_pin('EDS'+str(eds)+'PV'), GPIO.OUT)
    
for ctrl in ctrl_ids:
    GPIO.setup(test_master.get_pin('CTRL'+str(ctrl)+'PV'), GPIO.OUT)

# flag variables initialization
flip_on = True
temp_pass = False
humid_pass = False
schedule_pass = False
weather_pass = False
auto_pass = False

# error handling initialization
error_list = []
error_flag = False

# function to add error to errot list
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
#flag = False

while True:
    # set all flags to False
    temp_pass = False
    humid_pass = False
    schedule_pass = False
    weather_pass = False
    
    # MASTER TRY-EXCEPT -> will still allow RED LED to blink if fatal error occurs in loop
    try:
        '''
        --------------------------------------------------------------------------
        Clean up GPIO ports to initialize loop
        '''
        # switch power supply and EDS relays OFF (make sure this is always off unless testing)
        try:
            for eds in eds_ids:
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds)))
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds)+'PV'))
            for ctrl in ctrl_ids:
                GPIO.cleanup(test_master.get_pin('CTRL'+str(ctrl)+'PV'))
        except:
            add_error("GPIO-Cleanup")
            
        '''
        --------------------------------------------------------------------------
        Checking if RTC is working (initial check)
        '''
        try:
            current_time = rtc.datetime
            solar_offset = ceil(DM.get_solar_time(gmt_offset, current_time, longitude, latitude) * 100)/100
            
            # remove error if corrected
            if "Sensor-RTC-1" in error_list:
                error_list.remove("Sensor-RTC-1")
        except:
            add_error("Sensor-RTC-1")
        
        '''
        --------------------------------------------------------------------------
        Green LED Blinks if loop working
        '''
        # flip indicator GREEN LED to show proper working
        if flip_on:
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            time.sleep(1)
            flip_on = False
        else:
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            time.sleep(1)
            flip_on = True
        
        # code for power savings
        GPIO.output(test_master.get_pin('outPinLEDRed'), 0)

        '''
        --------------------------------------------------------------------------
        BEGIN SOLAR NOON DATA ACQUISITION CODE
        The following code handles the automated data acquisition of SCC values for each EDS and CTRL at solar noon each day
        Code outline:
        1) Check if current time matches solar noon
        2) If yes, then for each EDS and CTRL in sequence, do the following:
            2a) Measure Voc,Isc,Irradiance, Temp, Humidity from PV cell
            2b) Compute power, PR, and SR
            2c) Write data to CSV/text files
        3) Then activate EDS6 (the battery charger)
        '''
        
        # get current solar time, solar noon time, current time in minutes
        try:
            curr_dt = rtc.datetime
            yday = TM.Y_DAYS[curr_dt.tm_mon - 1] + curr_dt.tm_mday
            solar_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60 + solar_offset
            curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
            solar_noon_min = 720 + solar_offset
        except:
            add_error("Sensor-RTC-2")
        
        #print("solarnoon current time difference: "+str(abs(solar_noon_min - curr_time_min)))

        # if within 60 seconds of solar noon, run measurements
        if abs(solar_noon_min - curr_time_min) < 1:

            print_l(rtc.datetime, "Initiating Solar Noon Mode")
            
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
            
            # Initialize pre and post data dictionaries
            data = panel_data
            post_data = panel_data
            
            # Pre EDS Activation Panel Measurements
            for panel in panel_ids:
                # check the eds_number
                panel_num = panel['num']
                # check panel type eds/ctrl
                panel_type = panel['type']
                # get the date and time
                data[panel]['date_time'] = curr_dt
                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                data[panel]['temp'] = pan_temp
                # get humidity data
                data[panel]['humid'] = w_read[0]
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                data[panel]['gpoa']
                '''PRE EDS ACTIVATION MEASUREMENT'''
                # measure PRE EDS activation ocv and scc
                ocv_pre = 0
                scc_pre = 0
                if panel_type == 'eds':
                    [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                print_l(curr_dt, "PRE EDS Solar Noon OCV for " + panel + ": " + str(ocv_pre))
                print_l(curr_dt, "PRE EDS Solar Noon SCC for " + panel + ": " + str(scc_pre))
                data[panel]['ocv_pre'] = ocv_pre
                data[panel]['scc_pre'] = scc_pre
                # compute the PRE EDS activation power measurements for each panel
                power_pre = pow_master.get_power_out(ocv_pre,scc_pre,pan_temp)
                print_l(curr_dt, "PRE EDS Solar Noon Power for " + panel + ": " + str(power_pre))
                data[panel]['pwr_pre'] = power_pre
                # compute the PRE EDS activation PR measurements for each panel
                pr_pre = pr_master.get_pr(ocv_pre,scc_pre,pan_temp,power_pre,g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon PR for " + panel + ": " + str(pr_pre))
                data[panel]['pr_pre'] = pr_pre
                # compute the PRE EDS activation SR measurements for each panel
                sr_pre = soil_master.get_sr(scc_pre, g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon SR for " + panel + ": " + str(sr_pre))
                data[panel]['sr_pre'] = sr_pre
                '''EDS activation'''
                # turn on GREEN LED for duration of EDS activation
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                # activate the EDS film if it is an eds panel
                if panel_type == 'eds':
                    test_master.run_test(panel_num)
                # turn off GREEN LED after test
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
                '''POST EDS ACTIVATION MEASUREMENT'''
                # measure POST EDS activation ocv and scc
                ocv_post = 0
                scc_post = 0
                if panel_type == 'eds':
                    [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                print_l(curr_dt, "POST EDS Solar Noon OCV for " + panel + ": " + str(ocv_post))
                print_l(curr_dt, "POST EDS Solar Noon SCC for " + panel + ": " + str(scc_post))
                data[panel]['ocv_post'] = ocv_post
                data[panel]['scc_post'] = scc_post
                # compute the POST EDS activation power measurements for each panel
                power_post = pow_master.get_power_out(ocv_post,scc_post,pan_temp)
                print_l(curr_dt, "POST EDS Solar Noon Power for " + panel + ": " + str(power_post))
                data[panel]['pwr_post'] = power_post
                # compute the POST EDS activation PR measurements for each panel
                pr_post = pr_master.get_pr(ocv_post,scc_post,pan_temp,power_post,g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon PR for " + panel + ": " + str(pr_post))
                data[panel]['pr_post'] = pr_post
                # compute the POST EDS activation SR measurements for each panel
                sr_post = soil_master.get_sr(scc_post, g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon SR for " + panel + ": " + str(sr_post))
                data[panel]['sr_post'] = sr_post
                # write data to csv file
                csv_master.write_noon_data(data[panel])
                # delay before changing to next EDS panel
                time.sleep(10)


            '''
            # (1) EDS Panels Pre-EDS Activation Measurements
            for eds in eds_ids:
                eds_ocv_pre = 0
                eds_scc_pre = 0
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                # measure ocv and scc
                [eds_ocv_pre, eds_scc_pre] = test_master.run_measure_EDS(eds)
                print_l(curr_dt, "PRE EDS Solar Noon OCV for EDS" + str(eds) + ": " + str(eds_ocv_pre))
                print_l(curr_dt, "PRE EDS Solar Noon SCC for EDS" + str(eds) + ": " + str(eds_scc_pre))
                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                # compute the power measurements for each panel
                eds_power_pre = pow_master.get_power_out(eds_ocv_pre,eds_scc_pre,pan_temp)
                print_l(curr_dt, "PRE EDS Solar Noon Power for EDS" + str(eds) + ": " + str(eds_power_pre))
                # compute the PR measurements for each panel
                eds_pr_pre = pr_master.get_pr(eds_ocv_pre,eds_scc_pre,pan_temp,eds_power_pre,g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon PR for EDS" + str(eds) + ": " + str(eds_pr_pre))
                # compute the SR measurements for each panel
                eds_sr_pre = soil_master.get_sr(eds_scc_pre, g_poa)
                print_l(curr_dt, "PRE EDS Solar Noon SR for EDS" + str(eds) + ": " + str(eds_sr_pre))
                # write data to solar noon csv/txt
                eds_num = "EDS"+str(eds)
                # write data to csv file
                #csv_master.write_noon_data(curr_dt, w_read[1], w_read[0], g_poa, eds_act, eds_num, eds_ocv_pre, eds_scc_pre, eds_power_pre, eds_pr_pre, eds_sr_pre)
                # delay before changing to next EDS panel
                time.sleep(5)
            
            # (2) CTRL Panels Pre-EDS Activation Measurements
            for ctrl in ctrl_ids:
                ctrl_ocv_pre = 0
                ctrl_scc_pre = 0
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                # measure the ocv and scc
                [ctrl_ocv_pre, ctrl_scc_pre] = test_master.run_measure_CTRL(ctrl)
                print_l(curr_dt, "PRE Solar Noon OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_pre))
                print_l(curr_dt, "PRE Solar Noon SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_pre))
                # get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                # compute the measurements for each panel
                ctrl_power_pre = pow_master.get_power_out(ctrl_ocv_pre,ctrl_scc_pre,pan_temp)
                print_l(curr_dt, "PRE Solar Noon Power for CTRL" + str(ctrl) + ": " + str(ctrl_power_pre))
                # compute the PR measurements for each panel
                ctrl_pr_pre = pr_master.get_pr(ctrl_ocv_pre,ctrl_scc_pre,pan_temp,ctrl_power_pre,g_poa)
                print_l(curr_dt, "PRE Solar Noon PR for CTRL" + str(ctrl) + ": " + str(ctrl_pr_pre))
                # compute the SR measurements for each panel
                ctrl_sr = soil_master.get_sr(ctrl_scc_pre,g_poa)
                print_l(curr_dt, "PRE Solar Noon SR for CTRL" + str(ctrl) + ": " + str(ctrl_sr_pre))
                # write data to solar noon csv/txt
                ctrl_num = "CTRL"+str(ctrl)
                # write data to csv file
                #csv_master.write_noon_data(curr_dt, w_read[1], w_read[0], g_poa, eds_act,ctrl_num, ctrl_ocv, ctrl_scc, ctrl_power, ctrl_pr, ctrl_sr)
                # delay before changing to next CTRL panel
                time.sleep(5)
            
            # (3) EDS Activation For All Panels
            # turn on GREEN LED for duration of EDS activation
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            # run test
            test_master.activate_eds(eds_ids)
            # turn off GREEN LED after test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)

            # (4) EDS Panels Post-EDS Activation Measurements
            for eds in eds_ids:
                eds_ocv_post = 0
                eds_scc_post = 0
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                # measure the ocv and scc
                [eds_ocv_post, eds_scc_post] = test_master.run_measure_EDS(eds)
                print_l(curr_dt, "POST EDS Solar Noon OCV for EDS" + str(eds) + ": " + str(eds_ocv_post))
                print_l(curr_dt, "POST EDS Solar Noon SCC for EDS" + str(eds) + ": " + str(eds_scc_post))
                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                # compute the measurements for each panel
                eds_power_post = pow_master.get_power_out(eds_ocv_post,eds_scc_post,pan_temp)
                print_l(curr_dt, "POST EDS Solar Noon Power for EDS" + str(eds) + ": " + str(eds_power_post))
                # compute the PR measurements for each panel
                eds_pr_post = pr_master.get_pr(eds_ocv_post,eds_scc_post,pan_temp,eds_power_post,g_poa)
                print_l(curr_dt, "POST EDS Solar Noon PR for EDS" + str(eds) + ": " + str(eds_pr_post))
                # compute the SR measurements for each panel
                eds_sr_post = soil_master.get_sr(eds_scc_post,g_poa)
                print_l(curr_dt, "POST EDS Solar Noon SR for EDS" + str(eds) + ": " + str(eds_sr_post))
                # write data to solar noon csv/txt
                eds_num = "EDS"+str(eds)
                eds_act = "POST"
                # write data to csv file
                #csv_master.write_noon_data(curr_dt, w_read[1], w_read[0], g_poa, eds_act, eds_num, eds_ocv_post, eds_scc_post, eds_power_post, eds_pr_post, eds_sr_post)
                # delay before changing to next EDS panel
                time.sleep(5)
            
            # (6) write the data on csv files
            csv_master.write_noon_data(curr_dt)
            
            # 7) delay for each solar noon activation
            print("Completed Solar Noon Activation! Starting 3 min delay")
            time.sleep(180)
            '''

        '''
        END SOLAR NOON DATA ACQUISITION CODE
        --------------------------------------------------------------------------
        '''
        
        '''
        --------------------------------------------------------------------------
        Checking the operational time for automatic testing mode 9AM-14PM
        '''
        current_dt=rtc.datetime
        if current_dt.tm_hour > 8 or current_dt.tm_hour < 11:
            auto_pass = True
        elif current_dt.tm_hour > 14 or current_dt.tm_hour < 17:
            auto_pass = True
        else:
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            auto_pass = False
        '''
        --------------------------------------------------------------------------
        BEGIN AUTOMATIC TESTING ACTIVATION CODE
        The following code handles the automated activation of the each EDS as specified by their schedule in config.txt
        Code outline:
        For each EDS in sequence, do the following:
        1) Check if current time matches scheduled activation time for EDS
        2) If yes, check if current weather matches testing weather parameters, within activation window
        3) If yes, run complete testing procedure for that EDS
            3a) Measure OCV and SCC for control PV cells
            3b) Measure [before] OCV and SCC for EDS PV being tested
            3c) Flip relays to activate EDS for test duration
            3d) Measure [after] OCV and SCC for EDS PV being tested
            3e) Write data to CSV/txt files
        '''
        # TO DISABLE AUTOMATIC TESTING MODE, UNCOMMENT BELOW
        #auto = False

        # put EDS in a queue if multiple are to be activated simultaneously
        eds_testing_queue = []
        
        for eds_num in eds_ids:
            schedule_pass = test_master.check_time(curr_dt, yday, 0, eds_num)
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
            weather_pass = temp_pass and humid_pass and auto_pass
            
            while window < test_master.get_param('testWindowSeconds') and not weather_pass:
                # increment window by 1 sec
                window += 1
                time.sleep(1)
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

                # turn green LED on to show automatic testing is operating
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                flip_on = False

                #1 minute delay per panel
                time.sleep(60)

                # run testing procedure
                curr_dt = rtc.datetime
                
                # 1) get control OCV and SCC  values for each control
                ctrl_ocv_data = []
                ctrl_scc_data = []
                for ctrl in ctrl_ids:
                    ocv = 0
                    scc = 0
                    [ocv, scc] = test_master.run_measure_CTRL(ctrl)
                    ctrl_ocv_data.append(ocv)
                    ctrl_scc_data.append(scc)
                    print_l(rtc.datetime, "OCV for CTRL" + str(ctrl) + ": " + str(ctrl_ocv_data[ctrl - 1]))
                    print_l(rtc.datetime, "SCC for CTRL" + str(ctrl) + ": " + str(ctrl_scc_data[ctrl - 1]))
                                
                # 2) get OCV and SCC 'before' value for EDS being tested
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
                
                # 4) get OCV and SCC of PV 'after' value for EDS being tested
                [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds)
                print_l(rtc.datetime, "Post-test OCV for EDS" + str(eds) + ": " + str(eds_ocv_after))
                print_l(rtc.datetime, "Post-test SCC for EDS" + str(eds) + ": " + str(eds_scc_after))
                
                # 5) compile all measurements for eds and control
                # write data for EDS tested
                data_ocv_scc = [eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after]
                # append control data
                for ctrl in ctrl_ids:
                    data_ocv_scc.append(ctrl_ocv_data[ctrl - 1])
                    data_ocv_scc.append(ctrl_scc_data[ctrl - 1])

                # 6) get readings from the SP420 pyranometer
                irr_master = SP420.Irradiance()
                g_poa =irr_master.get_irradiance()
                print_l(rtc.datetime, "Global Irradiance " + "EDS" + str(eds) + ": " + str(g_poa))
                
                # 7) compute the power output from the v_oc and i_sc measurements
                #initialize empty list
                power_data = []

                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                
                # compute the measurements for each panel
                eds_power_before = pow_master.get_power_out(eds_ocv_before,eds_scc_before,pan_temp)
                eds_power_after = pow_master.get_power_out(eds_ocv_after,eds_scc_after,pan_temp)
                ctrl1_power = pow_master.get_power_out(data_ocv_scc[4],data_ocv_scc[5],pan_temp)
                ctrl2_power = pow_master.get_power_out(data_ocv_scc[6],data_ocv_scc[7],pan_temp)
                
                # compile the results to the list
                power_data.append(eds_power_before)
                power_data.append(eds_power_after)
                power_data.append(ctrl1_power)
                power_data.append(ctrl2_power)
                
                # print and log the power values
                print_l(rtc.datetime, "Pre-test Power for EDS" + str(eds) + ": " + str(eds_power_before))
                print_l(rtc.datetime, "Post-test Power for EDS" + str(eds) + ": " + str(eds_power_after))
                print_l(rtc.datetime, "Power for CTRL1" + ": " + str(ctrl1_power))
                print_l(rtc.datetime, "Power for CTRL2" + ": " + str(ctrl2_power))

                # 8) soiling ratio measurements
                
                # 9) finish up, write data to CSV
                csv_master.write_testing_data(curr_dt, w_read[1], w_read[0], g_poa, eds, data_ocv_scc, power_data)
                print_l(rtc.datetime, "Ended automated scheduled test of EDS" + str(eds))

                # 10) turn of green LED to show testing is done
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
                flip_on = True

        '''
        END AUTOMATIC TESTING ACTIVATION CODE
        --------------------------------------------------------------------------
        '''

        '''
        --------------------------------------------------------------------------
        BEGIN MANUAL ACTIVATION CODE
        The following code handles the manual activation of the specified EDS (in config.json) by flipping the switch
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
            eds_num = test_master.get_pin('manualEDSNumber')
            
            # get weather and time for data logging
            curr_dt = rtc.datetime
            w_read = weather.read_humidity_temperature()
            
            # solid GREEN for duration of manual test
            GPIO.output(test_master.get_pin('outPinLEDGreen'), GPIO.HIGH)
            print_l(rtc.datetime, "FORCED. Running EDS" + str(eds_num) + " testing sequence. FLIP SWITCH OFF TO STOP.")
            try:
                # Get global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                print_l(rtc.datetime, "GPOA Measurement for EDS " + str(eds_num) + ": " + str(g_poa))

                # measure PV voc and isc before EDS activation
                [eds_ocv_before, eds_scc_before] = test_master.run_measure_EDS(eds_num)
                print_l(rtc.datetime, "Pre-test OCV for EDS" + str(eds_num) + ": " + str(eds_ocv_before))
                print_l(rtc.datetime, "Pre-test SCC for EDS" + str(eds_num) + ": " + str(eds_scc_before))

                # get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                
                # compute the power measurements for each panel
                eds_power_before = pow_master.get_power_out(eds_ocv_before,eds_scc_before,pan_temp)
                print_l(curr_dt, "Pre-EDS Manual Activation Power Calculation for EDS" + str(eds_num) + ": " + str(eds_power_before))

                # compute the PR before eds activation
                eds_pr_before = pr_master.get_pr(eds_ocv_before,eds_scc_before,pan_temp,eds_power_before,g_poa)
                print_l(curr_dt, "Pre-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_before))

                # compute the SR before eds activation
                eds_sr_before = soil_master.get_sr(eds_scc_before, g_poa)
                print_l(curr_dt, "Pre-EDS Manual Activation SR Calculation for EDS" + str(eds_num) + ": " + str(eds_sr_before))

                # activate the EDS film
                test_master.run_test(eds_num)

                # measure PV voc and isc after EDS activation
                [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds_num)
                print_l(rtc.datetime, "Post-EDS Manual Activation OCV for EDS" + str(eds_num) + ": " + str(eds_ocv_after))
                print_l(rtc.datetime, "Post-EDS Manual Activation SCC for EDS" + str(eds_num) + ": " + str(eds_scc_after))
                
                # get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                
                # compute the power measurements Post EDS
                eds_power_after = pow_master.get_power_out(eds_ocv_after,eds_scc_after,pan_temp)
                print_l(curr_dt, "Post-EDS Manual Activation Power for EDS" + str(eds_num) + ": " + str(eds_power_after))
                
                # compute the PR measurement Post EDS                       # compute the PR before eds activation
                eds_pr_after = pr_master.get_pr(eds_ocv_after,eds_scc_after,pan_temp,eds_power_after,g_poa)
                print_l(curr_dt, "Post-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_after))

                # compute the SR before eds activation
                eds_sr_after = soil_master.get_sr(eds_scc_after, g_poa)
                print_l(curr_dt, "Post-EDS Manual Activation SR Calculation for EDS" + str(eds_num) + ": " + str(eds_sr_after))

                # compile data
                man_power_data = [eds_power_before,eds_power_after]
                man_pr_data = [eds_pr_before,eds_pr_after]
                man_sr_data = [eds_sr_before, eds_sr_after]

                # write data for EDS tested
                csv_master.write_manual_data(curr_dt, w_read[1], w_read[0], g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, man_power_data, man_pr_data, man_sr_data)
                print_l(rtc.datetime, "Ended Manual Activation Test of EDS" + str(eds_num))
            
            except:
                print_l(rtc.datetime, "Error with manual testing sequence. Please check.")
                add_error("Test-Manual")
        
            # either way, turn off GREEN LED indicator
            GPIO.output(test_master.get_pin('outPinLEDGreen'),GPIO.LOW)
    
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
    time.sleep(1)
    # END CORE LOOP