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
test_master = TM.TestingMaster(static_master.get_config())
usb_master = DM.USBMaster()
print(usb_master.get_USB_path())

# setup sensors
weather = AM2315.AM2315()
i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

# creating initial files to usb
print("Setting up initial CSV and TXT files in USB if not exist yet")
usb_master.setup_usb_mount()
csv_master = DM.CSVMaster(usb_master.get_USB_path())
log_master = DM.LogMaster(usb_master.get_USB_path(), rtc.datetime)
usb_master.reset_usb_mounts()

# initialize measurement classes
adc_master = TM.ADCMaster()
pow_master = TM.PowerMaster()
pr_master = TM.PerformanceRatio()
soil_master = TM.Soiling()

# id variables for test coordination
eds_ids = test_master.get_config()['EDSIDS']
ctrl_ids = test_master.get_config()['CTRLIDS']
panel_ids = test_master.get_config()['PANELIDS']
panel_data = static_master.get_panel_data()

# location data for easy use in solar time calculation
gmt_offset = test_master.get_param('offsetGMT')
longitude = test_master.get_param('degLongitude')
latitude = 1 # latitude currently unused

# channel setups
GPIO.setmode(GPIO.BCM)

# LED port setup
GPIO.setup(test_master.get_pin('outPinLEDGreen'), GPIO.OUT)
GPIO.setup(test_master.get_pin('outPinLEDRed'), GPIO.OUT)
GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)

# manual button port setup
GPIO.setup(test_master.get_pin('inPinManualActivate'), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(test_master.get_pin('inPinManualActivate'), GPIO.RISING)

# adc chip port setup
GPIO.setup(test_master.get_pin('ADC'), GPIO.OUT)

# for each EDS, CTRL id, set up GPIO channel
for eds in range(len(eds_ids)):
    GPIO.setup(test_master.get_pin('EDS'+str(eds+1)), GPIO.OUT)
    GPIO.setup(test_master.get_pin('EDS'+str(eds+1)+'PV'), GPIO.OUT)
    
for ctrl in range(len(ctrl_ids)):
    GPIO.setup(test_master.get_pin('CTRL'+str(ctrl+1)+'PV'), GPIO.OUT)

# flag variables initialization
flip_on = True
temp_pass = False
humid_pass = False
weather_pass = False
auto_pass = False

# error handling initialization
error_list = []
error_flag = False

# time display functions
def print_time(dt):
    print(str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec), end='')

# function to print to log file
def print_l(dt, phrase):
    print_time(dt)
    print(" " + phrase)
    log_master.write_log(dt, phrase)

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


'''
~~~CORE LOOP~~~
This loop governs the overall code for the long term remote testing of the field units
1) Checks the time of day
2) Checks the temperature and humidity before testing
3) Runs testing sequence
4) Writes data to log files
5) Alerts in the case of an error
'''

while True:
    
    # MASTER TRY-EXCEPT -> will still allow RED LED to blink if fatal error occurs in loop
    try:
        '''
        --------------------------------------------------------------------------
        Clean up GPIO ports to initialize loop
        --------------------------------------------------------------------------
        '''
        # switch power supply and EDS relays OFF (make sure this is always off unless testing)
        try:
            for eds in range(len(eds_ids)):
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds+1)))
                GPIO.cleanup(test_master.get_pin('EDS'+str(eds+1)+'PV'))
            for ctrl in range(len(ctrl_ids)):
                GPIO.cleanup(test_master.get_pin('CTRL'+str(ctrl+1)+'PV'))
        except:
            add_error("GPIO-Cleanup")
            
        '''
        --------------------------------------------------------------------------
        Checking if RTC is working (initial check)
        --------------------------------------------------------------------------
        '''
        solar_offset = ceil(DM.get_solar_time(gmt_offset,longitude, rtc.datetime) * 100)/100
        try:
            current_time = rtc.datetime
            #solar_offset = ceil(DM.get_solar_time(gmt_offset, current_time, longitude, latitude) * 100)/100
            
            # remove error if corrected
            if "Sensor-RTC-1" in error_list:
                error_list.remove("Sensor-RTC-1")
        except:
            add_error("Sensor-RTC-1")
        
        '''
        --------------------------------------------------------------------------
        Green LED Blinks if loop working
        --------------------------------------------------------------------------
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
        New Scheduling Measurement Process
        --------------------------------------------------------------------------
        '''

        # check temp and humidity until they fall within parameter range or max window reached
        window = 0
        w_read = weather.read_humidity_temperature()
        temp_pass = test_master.check_temp(w_read[1])
        humid_pass = test_master.check_humid(w_read[0])
        weather_pass = temp_pass and humid_pass
        
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

        # if weather and time checks pass, do automatic testing mode measurements
        if weather_pass:
            # Initialize pre and post data dictionaries
            data = panel_data
            # mount the usb for data collection
            if usb_master.check_usb() == True:
                # mounts the usb
                usb_master.setup_usb_mount()
            else:
                print_l(rtc.datetime, "No USB Detected!")
                usb_master.reset()
            # turn green and red LED on to show automatic testing is operating
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            # Pre EDS Activation Panel Measurements
            for eds in eds_ids:
                '''EDS PANEL MEASUREMENT'''
                # start the measurement process
                print_l(rtc.datetime, "Weather check passed. Now proceeding for time check for " + eds + " panel")
                # check for the schedule
                freq = data[eds]['frequency']
                sched = data[eds]['schedule']
                eds_panel = SM.ScheduleMaster(eds, freq, sched, longitude, gmt_offset)
                schedule_pass = eds_panel.check_time(rtc.datetime)
                # check for frequency check
                frequency_pass = eds_panel.check_frequency(rtc.datetime)
                if schedule_pass and frequency_pass:
                    # start the measurement process
                    print_l(rtc.datetime, "Weather, schedule, and frequency checks passed. Initiating testing procedure for " + eds + " panel")
                    # check the eds_number
                    panel_num = data[eds]['num']
                    # get the date and time
                    data[eds]['date_time'] = rtc.datetime
                    # measure global irradiance data from pyranometer
                    irr_master = SP420.Irradiance()
                    g_poa = irr_master.get_irradiance()
                    data[eds]['gpoa'] = g_poa
                    print_l(rtc.datetime, "GPOA Irradiance for " + eds + ": " + str(g_poa))
                    #get the panel temperature using ambient temperature
                    amb_temp = w_read[1]
                    pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                    data[eds]['temp'] = pan_temp
                    # get humidity data
                    data[eds]['humid'] = w_read[0]
                    '''PRE EDS ACTIVATION MEASUREMENT'''
                    # measure PRE EDS activation ocv and scc
                    ocv_pre = 0
                    scc_pre = 0
                    [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                    print_l(rtc.datetime, "PRE EDS OCV for " + eds + ": " + str(ocv_pre))
                    print_l(rtc.datetime, "PRE EDS SCC for " + eds + ": " + str(scc_pre))
                    data[eds]['ocv_pre'] = ocv_pre
                    data[eds]['scc_pre'] = scc_pre
                    # compute the PRE EDS activation power measurements for each panel
                    power_pre = pow_master.get_power_out(ocv_pre,scc_pre,pan_temp)
                    print_l(rtc.datetime, "PRE EDS Power for " + eds + ": " + str(power_pre))
                    data[eds]['pwr_pre'] = power_pre
                    # compute the PRE EDS activation PR measurements for each panel
                    pr_pre = pr_master.get_pr(ocv_pre,scc_pre,pan_temp,power_pre,g_poa)
                    print_l(rtc.datetime, "PRE EDS PR for " + eds + ": " + str(pr_pre))
                    data[eds]['pr_pre'] = pr_pre
                    # compute the PRE EDS activation SR measurements for each panel
                    sr_pre = soil_master.get_sr(scc_pre, g_poa)
                    print_l(rtc.datetime, "PRE EDS SR for " + eds + ": " + str(sr_pre))
                    data[eds]['sr_pre'] = sr_pre
                    '''EDS ACTIVATION'''
                    # activate the EDS film if it is an eds panel
                    test_master.run_test(panel_num)
                    print_l(rtc.datetime, "Activating EDS for " + eds + " panel")
                    '''POST EDS ACTIVATION MEASUREMENT'''
                    # measure POST EDS activation ocv and scc
                    ocv_post = 0
                    scc_post = 0
                    [ocv_post, scc_post] = test_master.run_measure_EDS(panel_num)
                    print_l(rtc.datetime, "POST EDS OCV for " + eds + ": " + str(ocv_post))
                    print_l(rtc.datetime, "POST EDS SCC for " + eds + ": " + str(scc_post))
                    data[eds]['ocv_post'] = ocv_post
                    data[eds]['scc_post'] = scc_post
                    # compute the POST EDS activation power measurements for each panel
                    power_post = pow_master.get_power_out(ocv_post,scc_post,pan_temp)
                    print_l(rtc.datetime, "POST EDS Power for " + eds + ": " + str(power_post))
                    data[eds]['pwr_post'] = power_post
                    # compute the POST EDS activation PR measurements for each panel
                    pr_post = pr_master.get_pr(ocv_post,scc_post,pan_temp,power_post,g_poa)
                    print_l(rtc.datetime, "POST EDS PR for " + eds + ": " + str(pr_post))
                    data[eds]['pr_post'] = pr_post
                    # compute the POST EDS activation SR measurements for each panel
                    sr_post = soil_master.get_sr(scc_post, g_poa)
                    print_l(rtc.datetime, "POST EDS SR for " + eds + ": " + str(sr_post))
                    data[eds]['sr_post'] = sr_post
                    # write data to csv file
                    csv_master.write_testing_data(data[eds])
                    print_l(rtc.datetime, "Writing Automatic Testing Mode Measurements Results To CSV and TXT Files")
                    # delay before changing to next EDS panel
                    time.sleep(10)
                    '''CTRL PANEL MEASUREMENTS'''
                    for ctrl in ctrl_ids:
                        # start the measurement process
                        print_l(rtc.datetime, "Measuring Control Panels. Initiating testing procedure for " + ctrl + " panel")
                        # check the eds_number
                        panel_num = data[ctrl]['num']
                        # get the date and time
                        data[ctrl]['date_time'] = rtc.datetime
                        # measure global irradiance data from pyranometer
                        irr_master = SP420.Irradiance()
                        g_poa = irr_master.get_irradiance()
                        data[ctrl]['gpoa'] = g_poa
                        print_l(rtc.datetime, "GPOA Irradiance for " + ctrl + ": " + str(g_poa))
                        #get the panel temperature using ambient temperature
                        amb_temp = w_read[1]
                        pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                        data[ctrl]['temp'] = pan_temp
                        # get humidity data
                        data[ctrl]['humid'] = w_read[0]
                        '''PRE EDS ACTIVATION MEASUREMENT'''
                        # measure PRE EDS activation ocv and scc
                        ocv_pre = 0
                        scc_pre = 0
                        [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                        print_l(rtc.datetime, "PRE EDS OCV for " + ctrl + ": " + str(ocv_pre))
                        print_l(rtc.datetime, "PRE EDS SCC for " + ctrl + ": " + str(scc_pre))
                        data[ctrl]['ocv_pre'] = ocv_pre
                        data[ctrl]['scc_pre'] = scc_pre
                        # compute the PRE EDS activation power measurements for each panel
                        power_pre = pow_master.get_power_out(ocv_pre,scc_pre,pan_temp)
                        print_l(rtc.datetime, "PRE EDS Power for " + ctrl + ": " + str(power_pre))
                        data[ctrl]['pwr_pre'] = power_pre
                        # compute the PRE EDS activation PR measurements for each panel
                        pr_pre = pr_master.get_pr(ocv_pre,scc_pre,pan_temp,power_pre,g_poa)
                        print_l(rtc.datetime, "PRE EDS PR for " + ctrl + ": " + str(pr_pre))
                        data[ctrl]['pr_pre'] = pr_pre
                        # compute the PRE EDS activation SR measurements for each panel
                        sr_pre = soil_master.get_sr(scc_pre, g_poa)
                        print_l(rtc.datetime, "PRE EDS SR for " + ctrl + ": " + str(sr_pre))
                        data[ctrl]['sr_pre'] = sr_pre
                        '''NO EDS ACTIVATION'''
                        print_l(rtc.datetime, "Not Activating EDS for " + panel + " panel")
                        '''NO NEED POST EDS ACTIVATION MEASUREMENT'''
                        # write data to csv file
                        csv_master.write_testing_data(data[panel])
                        print_l(rtc.datetime, "Writing Results To CSV and TXT Files")
                        # delay before changing to next EDS panel
                        time.sleep(10)

            # un-mount the usb drive
            usb_master.reset_usb_mounts()
            # turn of RED LED, indicating USB can be swapped
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            # time to swap USB if desired
            print("Finished measuring all panels. Resuming loop in 10 sec")
            time.sleep(10)


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

        '''
        DELETE
        # get current solar time, solar noon time, current time in minutes
        try:
            #curr_dt = rtc.datetime
            #yday = TM.Y_DAYS[curr_dt.tm_mon - 1] + curr_dt.tm_mday
            #solar_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60 + solar_offset
            #curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
            solar_noon_min = 720 + solar_offset
        except:
            add_error("Sensor-RTC-2")
        
        #print("solarnoon current time difference: "+str(abs(solar_noon_min - curr_time_min)))
        '''

        # if within 60 seconds of solar noon, run measurements (20 min right now) 
        solar_noon_min = 720 + solar_offset
        curr_time_min = curr_dt.tm_hour * 60 + curr_dt.tm_min + curr_dt.tm_sec / 60
        if abs(solar_noon_min - curr_time_min) < 20:
            '''BEGIN SOLAR NOON MODE'''
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
            # mount the usb for data collection
            if usb_master.check_usb() == True:
                # mounts the usb
                usb_master.setup_usb_mount()
            else:
                print_l(rtc.datetime, "No USB Detected!")
                usb_master.reset()
            # turn on red and green LEDs, indicating it is measuring time
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            # Pre EDS Activation Panel Measurements
            for panel in panel_ids:
                # check the eds_number
                panel_num = data[panel]['num']
                # check panel type eds/ctrl
                panel_type = data[panel]['type']
                # get the date and time
                data[panel]['date_time'] = rtc.datetime
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                data[panel]['gpoa'] = g_poa
                print_l(rtc.datetime, "Noon Mode GPOA Irradiance for " + panel + ": " + str(g_poa))
                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                data[panel]['temp'] = pan_temp
                # get humidity data
                data[panel]['humid'] = w_read[0]
                '''PRE EDS ACTIVATION MEASUREMENT'''
                # measure PRE EDS activation ocv and scc
                ocv_pre = 0
                scc_pre = 0
                if panel_type == 'eds':
                    [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                print_l(rtc.datetime, "PRE EDS Solar Noon OCV for " + panel + ": " + str(ocv_pre))
                print_l(rtc.datetime, "PRE EDS Solar Noon SCC for " + panel + ": " + str(scc_pre))
                data[panel]['ocv_pre'] = ocv_pre
                data[panel]['scc_pre'] = scc_pre
                # compute the PRE EDS activation power measurements for each panel
                power_pre = pow_master.get_power_out(ocv_pre,scc_pre,pan_temp)
                print_l(rtc.datetime, "PRE EDS Solar Noon Power for " + panel + ": " + str(power_pre))
                data[panel]['pwr_pre'] = power_pre
                # compute the PRE EDS activation PR measurements for each panel
                pr_pre = pr_master.get_pr(ocv_pre,scc_pre,pan_temp,power_pre,g_poa)
                print_l(rtc.datetime, "PRE EDS Solar Noon PR for " + panel + ": " + str(pr_pre))
                data[panel]['pr_pre'] = pr_pre
                # compute the PRE EDS activation SR measurements for each panel
                sr_pre = soil_master.get_sr(scc_pre, g_poa)
                print_l(rtc.datetime, "PRE EDS Solar Noon SR for " + panel + ": " + str(sr_pre))
                data[panel]['sr_pre'] = sr_pre
                '''EDS ACTIVATION'''
                # activate the EDS film if it is an eds panel
                if panel_type == 'eds':
                    test_master.run_test(panel_num)
                    print_l(rtc.datetime, "Activating EDS for " + panel + " panel")
                elif panel_type == 'ctrl':
                    print_l(rtc.datetime, "Not Activating EDS for " + panel + " panel")
                '''POST EDS ACTIVATION MEASUREMENT'''
                # measure POST EDS activation ocv and scc
                ocv_post = 0
                scc_post = 0
                if panel_type == 'eds':
                    [ocv_post, scc_post] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_post, scc_post] = test_master.run_measure_CTRL(panel_num)
                print_l(rtc.datetime, "POST EDS Solar Noon OCV for " + panel + ": " + str(ocv_post))
                print_l(rtc.datetime, "POST EDS Solar Noon SCC for " + panel + ": " + str(scc_post))
                data[panel]['ocv_post'] = ocv_post
                data[panel]['scc_post'] = scc_post
                # compute the POST EDS activation power measurements for each panel
                power_post = pow_master.get_power_out(ocv_post,scc_post,pan_temp)
                print_l(rtc.datetime, "POST EDS Solar Noon Power for " + panel + ": " + str(power_post))
                data[panel]['pwr_post'] = power_post
                # compute the POST EDS activation PR measurements for each panel
                pr_post = pr_master.get_pr(ocv_post,scc_post,pan_temp,power_post,g_poa)
                print_l(rtc.datetime, "POST EDS Solar Noon PR for " + panel + ": " + str(pr_post))
                data[panel]['pr_post'] = pr_post
                # compute the POST EDS activation SR measurements for each panel
                sr_post = soil_master.get_sr(scc_post, g_poa)
                print_l(rtc.datetime, "POST EDS Solar Noon SR for " + panel + ": " + str(sr_post))
                data[panel]['sr_post'] = sr_post
                # write data to csv file
                csv_master.write_noon_data(data[panel])
                print_l(rtc.datetime, "Writing Noon Mode Measurements Results To CSV and TXT Files")
                # delay before changing to next panel
                time.sleep(10)
            # un-mount the usb drive
            usb_master.reset_usb_mounts()
            # turn of RED LED, indicating USB can be swapped
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            # time to swap USB if desired
            print("Finished measuring all panels. Resuming loop in 10 sec")
            time.sleep(10)

        '''
        END SOLAR NOON DATA ACQUISITION CODE
        --------------------------------------------------------------------------
        '''
        '''
        --------------------------------------------------------------------------
        Checking the operational time for automatic testing mode
        --------------------------------------------------------------------------
        '''
        current_dt=rtc.datetime
        if current_dt.tm_hour >= 9 and current_dt.tm_hour < 11:
            auto_pass = True
        elif current_dt.tm_hour >= 13 and current_dt.tm_hour < 17:
            auto_pass = True
        else:
            auto_pass = False
        
        # TO DISABLE AUTOMATIC TESTING MODE, UNCOMMENT BELOW
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
        # check temp and humidity until they fall within parameter range or max window reached
        window = 0
        w_read = weather.read_humidity_temperature()
        temp_pass = test_master.check_temp(w_read[1])
        humid_pass = test_master.check_humid(w_read[0])
        weather_pass = temp_pass and humid_pass
        
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
        
        # if weather and time checks pass, do automatic testing mode measurements
        if weather_pass and auto_pass:
            # Initialize pre and post data dictionaries
            data = panel_data
            # mount the usb for data collection
            if usb_master.check_usb() == True:
                # mounts the usb
                usb_master.setup_usb_mount()
            else:
                print_l(rtc.datetime, "No USB Detected!")
                usb_master.reset()
            # turn green and red LED on to show automatic testing is operating
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            # Pre EDS Activation Panel Measurements
            for panel in panel_ids:
                '''Begin Automatic Testing Mode'''
                # start the measurement process
                print_l(rtc.datetime, "Time and weather checks passed. Initiating testing procedure for " + panel + " panel")
                # check the eds_number
                panel_num = data[panel]['num']
                # check panel type eds/ctrl
                panel_type = data[panel]['type']
                # get the date and time
                data[panel]['date_time'] = rtc.datetime
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                data[panel]['gpoa'] = g_poa
                print_l(rtc.datetime, "Testing Mode GPOA Irradiance for " + panel + ": " + str(g_poa))
                #get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp,g_poa)
                data[panel]['temp'] = pan_temp
                # get humidity data
                data[panel]['humid'] = w_read[0]
                '''PRE EDS ACTIVATION MEASUREMENT'''
                # measure PRE EDS activation ocv and scc
                ocv_pre = 0
                scc_pre = 0
                if panel_type == 'eds':
                    [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                print_l(rtc.datetime, "PRE EDS Automatic Testing Mode OCV for " + panel + ": " + str(ocv_pre))
                print_l(rtc.datetime, "PRE EDS Automatic Testing Mode SCC for " + panel + ": " + str(scc_pre))
                data[panel]['ocv_pre'] = ocv_pre
                data[panel]['scc_pre'] = scc_pre
                # compute the PRE EDS activation power measurements for each panel
                power_pre = pow_master.get_power_out(ocv_pre,scc_pre,pan_temp)
                print_l(rtc.datetime, "PRE EDS Automatic Testing Mode Power for " + panel + ": " + str(power_pre))
                data[panel]['pwr_pre'] = power_pre
                # compute the PRE EDS activation PR measurements for each panel
                pr_pre = pr_master.get_pr(ocv_pre,scc_pre,pan_temp,power_pre,g_poa)
                print_l(rtc.datetime, "PRE EDS Automatic Testing Mode PR for " + panel + ": " + str(pr_pre))
                data[panel]['pr_pre'] = pr_pre
                # compute the PRE EDS activation SR measurements for each panel
                sr_pre = soil_master.get_sr(scc_pre, g_poa)
                print_l(rtc.datetime, "PRE EDS Automatic Testing Mode SR for " + panel + ": " + str(sr_pre))
                data[panel]['sr_pre'] = sr_pre
                '''EDS ACTIVATION'''
                # activate the EDS film if it is an eds panel
                if panel_type == 'eds':
                    test_master.run_test(panel_num)
                    print_l(rtc.datetime, "Activating EDS for " + panel + " panel")
                elif panel_type == 'ctrl':
                    print_l(rtc.datetime, "Not Activating EDS for " + panel + " panel")
                '''POST EDS ACTIVATION MEASUREMENT'''
                # measure POST EDS activation ocv and scc
                ocv_post = 0
                scc_post = 0
                if panel_type == 'eds':
                    [ocv_post, scc_post] = test_master.run_measure_EDS(panel_num)
                else:
                    [ocv_post, scc_post] = test_master.run_measure_CTRL(panel_num)
                print_l(rtc.datetime, "POST EDS Automatic Testing Mode OCV for " + panel + ": " + str(ocv_post))
                print_l(rtc.datetime, "POST EDS Automatic Testing Mode SCC for " + panel + ": " + str(scc_post))
                data[panel]['ocv_post'] = ocv_post
                data[panel]['scc_post'] = scc_post
                # compute the POST EDS activation power measurements for each panel
                power_post = pow_master.get_power_out(ocv_post,scc_post,pan_temp)
                print_l(rtc.datetime, "POST EDS Automatic Testing Mode Power for " + panel + ": " + str(power_post))
                data[panel]['pwr_post'] = power_post
                # compute the POST EDS activation PR measurements for each panel
                pr_post = pr_master.get_pr(ocv_post,scc_post,pan_temp,power_post,g_poa)
                print_l(rtc.datetime, "POST EDS Automatic Testing Mode PR for " + panel + ": " + str(pr_post))
                data[panel]['pr_post'] = pr_post
                # compute the POST EDS activation SR measurements for each panel
                sr_post = soil_master.get_sr(scc_post, g_poa)
                print_l(rtc.datetime, "POST EDS Automatic Testing Mode SR for " + panel + ": " + str(sr_post))
                data[panel]['sr_post'] = sr_post
                # write data to csv file
                csv_master.write_testing_data(data[panel])
                print_l(rtc.datetime, "Writing Automatic Testing Mode Measurements Results To CSV and TXT Files")
                # delay before changing to next EDS panel
                time.sleep(10)
            # un-mount the usb drive
            usb_master.reset_usb_mounts()
            # turn of RED LED, indicating USB can be swapped
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            # time to swap USB if desired
            print("Finished measuring all panels. Resuming loop in 10 sec")
            time.sleep(10)

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
            # mount the usb for data collection
            if usb_master.check_usb() == True:
                # mounts the usb
                usb_master.setup_usb_mount()
            else:
                print_l(rtc.datetime, "No USB Detected!")
                usb_master.reset()
            # turn green and red LED on to show measuring time
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            # run EDS test on selected manual EDS
            eds_num = test_master.get_pin('manualEDSNumber')
            # get weather and time for data logging
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
                print_l(rtc.datetime, "Pre-EDS Manual Activation Power Calculation for EDS" + str(eds_num) + ": " + str(eds_power_before))
                # compute the PR before eds activation
                eds_pr_before = pr_master.get_pr(eds_ocv_before,eds_scc_before,pan_temp,eds_power_before,g_poa)
                print_l(rtc.datetime, "Pre-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_before))
                # compute the SR before eds activation
                eds_sr_before = soil_master.get_sr(eds_scc_before, g_poa)
                print_l(rtc.datetime, "Pre-EDS Manual Activation SR Calculation for EDS" + str(eds_num) + ": " + str(eds_sr_before))
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
                print_l(rtc.datetime, "Post-EDS Manual Activation Power for EDS" + str(eds_num) + ": " + str(eds_power_after))
                # compute the PR measurement Post EDS                       # compute the PR before eds activation
                eds_pr_after = pr_master.get_pr(eds_ocv_after,eds_scc_after,pan_temp,eds_power_after,g_poa)
                print_l(rtc.datetime, "Post-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_after))
                # compute the SR before eds activation
                eds_sr_after = soil_master.get_sr(eds_scc_after, g_poa)
                print_l(rtc.datetime, "Post-EDS Manual Activation SR Calculation for EDS" + str(eds_num) + ": " + str(eds_sr_after))
                # compile data
                man_power_data = [eds_power_before,eds_power_after]
                man_pr_data = [eds_pr_before,eds_pr_after]
                man_sr_data = [eds_sr_before, eds_sr_after]
                # write data for EDS tested
                usb_master.check_USB()
                csv_master.write_manual_data(curr_dt, w_read[1], w_read[0], g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, man_power_data, man_pr_data, man_sr_data)
                print_l(rtc.datetime, "Writing Manual Testing Mode Measurements Results To CSV and TXT Files")
                print_l(rtc.datetime, "Ended Manual Activation Test of EDS" + str(eds_num))
            
            except:
                print_l(rtc.datetime, "Error with manual testing sequence. Please check.")
                add_error("Test-Manual")

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
        
    # error handling
    if not not error_list:
        e_phrase = "Current error list: "
        for err in error_list:
            e_phrase += " [" + err + "]"
        print_l(rtc.datetime, e_phrase)
        
    # blinking RED LED if error is raised
    if error_flag:
        if flip_on:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
        else:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0) 
    
    # END CORE LOOP