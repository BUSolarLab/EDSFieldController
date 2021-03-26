'''
=============================
Title: Master Control - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''

# dependencies
import RPi.GPIO as GPIO
import logging
import subprocess
import json
import datetime
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


print("Initializing...")
#initilize logging
logging.basicConfig(format='%(asctime)s %(message)s', filename = 'Error.log', level = logging.INFO)
logging.info('Code started')
# read config, get constants, etc
static_master = SM.StaticMaster()
test_master = TM.TestingMaster(static_master.get_config())
usb_master = DM.USBMaster()

#loop until a usb drive is inputted
while usb_mater.check_usb() == False
    print("USB not found! plug in a USB to continue")
    time.sleep(1)
print("USB found continuing... \n")
#set up usb
usb_master.set_USB_name()
usb_master.check_new_USB()
print(usb_master.get_USB_path())

# setup sensors
weather = AM2315.AM2315()
i2c_bus = busio.I2C(SCL, SDA)

# set up network or rtc time in a tuple format
def current_time():
    current_date = datetime.datetime.now()
    current_clock = time.struct_time((current_date.year, current_date.month,current_date.day, 
                                     current_date.hour, current_date.minute,
                                     current_date.second, 0, -1, -1))
    return current_clock

# creating initial csv and txt files to usb
print("Setting up initial CSV and TXT files in USB if not exist yet")
usb_master.setup_usb_mount()
csv_master = DM.CSVMaster(usb_master.get_USB_path())
log_master = DM.LogMaster(usb_master.get_USB_path(), current_time())
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
latitude = 1  # latitude currently unused

# RasPi board setup
GPIO.setmode(GPIO.BCM)

# LED port setup
GPIO.setup(test_master.get_pin('outPinLEDGreen'), GPIO.OUT)
GPIO.setup(test_master.get_pin('outPinLEDRed'), GPIO.OUT)
GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)

# manual button port setup
GPIO.setup(test_master.get_pin('inPinManualActivate'), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# old button setup
# GPIO.add_event_detect(test_master.get_pin('inPinManualActivate'), GPIO.RISING)

# adc chip port setup
GPIO.setup(test_master.get_pin('ADC'), GPIO.OUT)

# for each EDS, CTRL id, set up GPIO channel
for eds in range(len(eds_ids)):
    GPIO.setup(test_master.get_pin('EDS' + str(eds + 1)), GPIO.OUT)
    GPIO.setup(test_master.get_pin('EDS' + str(eds + 1) + 'PV'), GPIO.OUT)

for ctrl in range(len(ctrl_ids)):
    GPIO.setup(test_master.get_pin('CTRL' + str(ctrl + 1) + 'PV'), GPIO.OUT)

# flag variables initialization
flip_on = True
temp_pass = False
humid_pass = False
weather_pass = False
auto_pass = False
schedule_pass = False
frequency_pass = False
json_reset = False

# error handling initialization
error_list = []
error_flag = False


# time display functions
def print_time(dt):
    print(str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(
        dt.tm_min) + ':' + str(dt.tm_sec), end='')


# function to print formatted log into the log file
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
        print_l(current_time(), "ERROR FOUND: " + error)
    except Exception as e:
        # current_time() = time.struct_time((1,1,1,1,1,1,1,1,1))
        logging.exception( "Bad error %s",e)
        print_l(current_time(), "ERROR FOUND: " + error)


print("Starting FTU code Written by Aditya Brian and Ben...")
print_time(current_time())

'''
~~~CORE LOOP~~~
This loop governs the overall code for the long term remote testing of the field units
1) Check for weather, USB, schedule, and frequency
2) Run Sequence (measurement, activation, and measurement) an EDS panel
3) Save data to USB
4) Run measurement for both CTRL panels
5) Save data to USB
6) Repeat steps 1-5 for all the EDS panels
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
            #clean up pin for ocv isc as well
            GPIO.cleanup(25)
            for eds in range(len(eds_ids)):
                GPIO.cleanup(test_master.get_pin('EDS' + str(eds + 1)))
                GPIO.cleanup(test_master.get_pin('EDS' + str(eds + 1) + 'PV'))
            for ctrl in range(len(ctrl_ids)):
                GPIO.cleanup(test_master.get_pin('CTRL' + str(ctrl + 1) + 'PV'))
        except:
            add_error("GPIO-Cleanup")
        '''
        --------------------------------------------------------------------------
        Checking if RTC is working (initial check)
        --------------------------------------------------------------------------
        '''
        #get time in sec
        sec_old = current_time().tm_sec
        time.sleep(2)
        # get time in sec after 2 seconds
        sec_new = current_time().tm_sec
        # if the two times match there is an error
        if sec_old == sec_new :
            add_error("Sensor-RTC-1")
        else:
            # remove error if corrected and proceed to next code
            if "Sensor-RTC-1" in error_list:
                error_list.remove("Sensor-RTC-1")

        '''
        --------------------------------------------------------------------------
        Green LED Blinks if loop working, Red LED Off
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
        No Functionality if its at night (4PM - 9AM) to save power, just do LED blinking
        --------------------------------------------------------------------------
        '''
        #Get time from RTC or time sync from internet 
        current_dt = current_time()

        #Make this a while loop to reduce power consumtion
        if current_dt.tm_hour > 16 or current_dt.tm_hour < 9:
            day = False
            json_reset = True
        else:
            day = True
            json_reset = False

        if (current_dt.tm_hour == 12) and (current_dt.tm_min >= 0 and current_dt.tm_min < 2):
            noon = True
        else:
            noon = False

        '''
        --------------------------------------------------------------------------
        Field Test Unit Schedule for Measurement only
        --------------------------------------------------------------------------
        '''
        if noon: 
            print_l(current_time(), "Measurement only process starting...")
            # initialize weather and gpoa reading functions
            w_read = weather.read_humidity_temperature()
            # initialize panel data for measuerement
            data = panel_data
            # Control Measurements
            for ctrl in ctrl_ids:

                if usb_master.check_usb() == True:
                    # mounts the usb
                    usb_master.setup_usb_mount()
                else:
                    # if not, then reboot
                    print_l(current_time(), "No USB Detected!")
                    usb_master.reset()

                # turn green and red LED on to show automatic testing is operating
                # red LED on means USB should not be unplugged
                GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)

                # start the measurement process
                print_l(current_time(), "Time checked. Measurement procedure for " + ctrl + " panel")
                # check the eds_number
                panel_num = data[ctrl]['num']
                # get the date and time
                data[ctrl]['date_time'] = current_time()
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                data[ctrl]['gpoa'] = g_poa
                print_l(current_time(), "GPOA Irradiance for " + ctrl + ": " + str(g_poa))
                # get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
                data[ctrl]['temp'] = pan_temp
                # get humidity data
                data[ctrl]['humid'] = w_read[0]
                '''PRE EDS ACTIVATION MEASUREMENT'''
                # measure PRE EDS activation ocv and scc
                ocv_pre = 0
                scc_pre = 0
                [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                print_l(current_time(), "PRE EDS OCV for " + ctrl + ": " + str(ocv_pre))
                print_l(current_time(), "PRE EDS SCC for " + ctrl + ": " + str(scc_pre))
                data[ctrl]['ocv_pre'] = ocv_pre
                data[ctrl]['scc_pre'] = scc_pre
                # compute the PRE EDS activation power measurements for each panel
                power_pre = pow_master.get_power_out(ocv_pre, scc_pre, pan_temp)
                print_l(current_time(), "PRE EDS Power for " + ctrl + ": " + str(power_pre))
                data[ctrl]['pwr_pre'] = power_pre
                # compute the PRE EDS activation PR measurements for each panel
                pr_pre = pr_master.get_pr(ocv_pre, scc_pre, pan_temp, power_pre, g_poa)
                print_l(current_time(), "PRE EDS PR for " + ctrl + ": " + str(pr_pre))
                data[ctrl]['pr_pre'] = pr_pre
                # compute the PRE EDS activation SI measurements for each panel
                si_pre = soil_master.get_si(scc_pre, g_poa)
                print_l(current_time(), "PRE EDS SI for " + ctrl + ": " + str(si_pre))
                data[ctrl]['si_pre'] = si_pre

                # NO EDS ACTIVATION AND POST MEASUREMENTS FOR CTRL PANELS
                print_l(current_time(), "Not Activating EDS for " + ctrl + " panel")

                # SAVE DATA TO USB
                # write data to csv file
                csv_master.write_data(data[ctrl])
                print_l(current_time(), "Writing Results To CSV and TXT Files")
                # delay before changing to next EDS panel
                time.sleep(10)

            # Pre EDS Activation Panel Measurements for all eds
            for eds in eds_ids:
                # mount the usb for data collection if there is a USB plugged
                if usb_master.check_usb() == True:
                    # mounts the usb
                    usb_master.setup_usb_mount()
                else:
                    # if not, then reboot
                    print_l(current_time(), "No USB Detected!")
                    usb_master.reset()

                # turn green and red LED on to show automatic testing is operating
                # red LED on means USB should not be unplugged
                GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
                GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)

                # start the measurement process
                print_l(current_time(), "Time check passed. Measurement procedure for " + eds + " panel")
                # check the eds_number
                panel_num = data[eds]['num']
                # get the date and time
                data[eds]['date_time'] = current_time()
                # measure global irradiance data from pyranometer
                irr_master = SP420.Irradiance()
                g_poa = irr_master.get_irradiance()
                data[eds]['gpoa'] = g_poa
                print_l(current_time(), "GPOA Irradiance for " + eds + ": " + str(g_poa))
                # get the panel temperature using ambient temperature
                amb_temp = w_read[1]
                pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
                data[eds]['temp'] = pan_temp
                # get humidity data
                data[eds]['humid'] = w_read[0]

                # PRE EDS ACTIVATION MEASUREMENT
                # measure PRE EDS activation ocv and scc
                ocv_pre = 0
                scc_pre = 0
                [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                print_l(current_time(), "PRE EDS OCV for " + eds + ": " + str(ocv_pre))
                print_l(current_time(), "PRE EDS SCC for " + eds + ": " + str(scc_pre))
                data[eds]['ocv_pre'] = ocv_pre
                data[eds]['scc_pre'] = scc_pre
                # compute the PRE EDS activation power measurements for each panel
                power_pre = pow_master.get_power_out(ocv_pre, scc_pre, pan_temp)
                print_l(current_time(), "PRE EDS Power for " + eds + ": " + str(power_pre))
                data[eds]['pwr_pre'] = power_pre
                # compute the PRE EDS activation PR measurements for each panel
                pr_pre = pr_master.get_pr(ocv_pre, scc_pre, pan_temp, power_pre, g_poa)
                print_l(current_time(), "PRE EDS PR for " + eds + ": " + str(pr_pre))
                data[eds]['pr_pre'] = pr_pre
                # compute the PRE EDS activation SI measurements for each panel
                si_pre = soil_master.get_si(scc_pre, g_poa)
                print_l(current_time(), "PRE EDS SI for " + eds + ": " + str(si_pre))
                data[eds]['si_pre'] = si_pre

                # POST EDS ACTIVATION MEASUREMENT Not used instead put N/A
                ocv_post = 'N/A'
                scc_post = 'N/A'
                data[eds]['ocv_post'] = ocv_post
                data[eds]['scc_post'] = scc_post
                data[eds]['pwr_post'] = 'N/A'
                data[eds]['pr_post'] = 'N/A'
                data[eds]['si_post'] = 'N/A'

                # WRITE DATA TO USB
                # write data to csv file
                csv_master.write_data(data[eds])
                print_l(current_time(), "Writing Results To CSV and TXT Files")
                # delay before changing to control panels
                time.sleep(10)

            # un-mount the usb drive
            usb_master.reset_usb_mounts()
            # turn of RED LED, indicating USB can be swapped
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            # time to swap USB if desired
            time.sleep(10)

        '''
        --------------------------------------------------------------------------
        Field Test Unit Schedule for Measurement and Activation
        --------------------------------------------------------------------------
        '''
        # first check, if it is during the day
        if day:
            # Temperature Humidity Sensor Check
            w_read = weather.read_humidity_temperature()
            temp_pass = test_master.check_temp(w_read[1])
            humid_pass = test_master.check_humid(w_read[0])
            weather_pass = temp_pass and humid_pass
            # if weather and time checks pass, proceed to next check
            if weather_pass:
                # initialize panel data
                data = panel_data
                # Pre EDS Activation Panel Measurements
                for eds in eds_ids:
                    print_l(current_time(), " Weather check passed. Now proceeding for time check for " + eds + " panel")
                    # get data for frequency and schedule check for the current eds panel
                    freq = data[eds]['frequency']
                    sched = data[eds]['schedule']
                    # declare panel class, which gives the frequency and schedule checks
                    eds_panel = SM.ScheduleMaster(eds, freq, sched, longitude, gmt_offset)
                    # check for the schedule check
                    schedule_pass = eds_panel.check_time(current_time())
                    # check for frequency check only if it meets schedule check
                    if schedule_pass:
                        schedule_pass = True
                        print_l(current_time()," schedule passed for " + eds + " panel")
                        frequency_pass = eds_panel.check_frequency(eds, current_time())
                    # proceed to EDS measurement and activation process
                    if schedule_pass and frequency_pass:
                        print_l(current_time()," schedule and frequency passed for " + eds + " panel")
                        # mount the usb for data collection if there is a USB plugged
                        if usb_master.check_usb() == True:
                            # mounts the usb
                            usb_master.setup_usb_mount()
                        else:
                            # if not, then reboot
                            print_l(current_time(), "No USB Detected!")
                            usb_master.reset()
                        # turn green and red LED on to show automatic testing is operating
                        # red LED on means USB should not be unplugged
                        GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
                        GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
                        # start the measurement process
                        print_l(current_time(),
                                " Weather, schedule, and frequency checks passed. Initiating testing procedure for " + eds + " panel")
                        # check the eds_number
                        panel_num = data[eds]['num']
                        # get the date and time
                        data[eds]['date_time'] = current_time()
                        # measure global irradiance data from pyranometer
                        irr_master = SP420.Irradiance()
                        g_poa = irr_master.get_irradiance()
                        data[eds]['gpoa'] = g_poa
                        print_l(current_time(), "GPOA Irradiance for " + eds + ": " + str(g_poa))
                        # get the panel temperature using ambient temperature
                        amb_temp = w_read[1]
                        pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
                        data[eds]['temp'] = pan_temp
                        # get humidity data
                        data[eds]['humid'] = w_read[0]

                        # PRE EDS ACTIVATION MEASUREMENT
                        # measure PRE EDS activation ocv and scc
                        ocv_pre = 0
                        scc_pre = 0
                        [ocv_pre, scc_pre] = test_master.run_measure_EDS(panel_num)
                        print_l(current_time(), "PRE EDS OCV for " + eds + ": " + str(ocv_pre))
                        print_l(current_time(), "PRE EDS SCC for " + eds + ": " + str(scc_pre))
                        data[eds]['ocv_pre'] = ocv_pre
                        data[eds]['scc_pre'] = scc_pre
                        # compute the PRE EDS activation power measurements for each panel
                        power_pre = pow_master.get_power_out(ocv_pre, scc_pre, pan_temp)
                        print_l(current_time(), "PRE EDS Power for " + eds + ": " + str(power_pre))
                        data[eds]['pwr_pre'] = power_pre
                        # compute the PRE EDS activation PR measurements for each panel
                        pr_pre = pr_master.get_pr(ocv_pre, scc_pre, pan_temp, power_pre, g_poa)
                        print_l(current_time(), "PRE EDS PR for " + eds + ": " + str(pr_pre))
                        data[eds]['pr_pre'] = pr_pre
                        # compute the PRE EDS activation SI measurements for each panel
                        si_pre = soil_master.get_si(scc_pre, g_poa)
                        print_l(current_time(), "PRE EDS SI for " + eds + ": " + str(si_pre))
                        data[eds]['si_pre'] = si_pre

                        # EDS ACTIVATION
                        test_master.run_test(panel_num)
                        print_l(current_time(), "Activating EDS for " + eds + " panel")

                        # POST EDS ACTIVATION MEASUREMENT
                        # measure POST EDS activation ocv and scc
                        ocv_post = 0
                        scc_post = 0
                        [ocv_post, scc_post] = test_master.run_measure_EDS(panel_num)
                        print_l(current_time(), "POST EDS OCV for " + eds + ": " + str(ocv_post))
                        print_l(current_time(), "POST EDS SCC for " + eds + ": " + str(scc_post))
                        data[eds]['ocv_post'] = ocv_post
                        data[eds]['scc_post'] = scc_post
                        # compute the POST EDS activation power measurements for each panel
                        power_post = pow_master.get_power_out(ocv_post, scc_post, pan_temp)
                        print_l(current_time(), "POST EDS Power for " + eds + ": " + str(power_post))
                        data[eds]['pwr_post'] = power_post
                        # compute the POST EDS activation PR measurements for each panel
                        pr_post = pr_master.get_pr(ocv_post, scc_post, pan_temp, power_post, g_poa)
                        print_l(current_time(), "POST EDS PR for " + eds + ": " + str(pr_post))
                        data[eds]['pr_post'] = pr_post
                        # compute the POST EDS activation SI measurements for each panel
                        si_post = soil_master.get_si(scc_post, g_poa)
                        print_l(current_time(), "POST EDS SI for " + eds + ": " + str(si_post))
                        data[eds]['si_post'] = si_post

                        # WRITE DATA TO USB
                        # write data to csv file
                        csv_master.write_data(data[eds])
                        print_l(current_time(), "Writing Results To CSV and TXT Files")
                        # delay before changing to control panels
                        time.sleep(10)

                        # CTRL PANEL MEASUREMENTS
                        for ctrl in ctrl_ids:
                            # start the measurement process
                            print_l(current_time(),
                                    "Measuring Control Panels. Initiating testing procedure for " + ctrl + " panel")
                            # check the eds_number
                            panel_num = data[ctrl]['num']
                            # get the date and time
                            data[ctrl]['date_time'] = current_time()
                            # measure global irradiance data from pyranometer
                            irr_master = SP420.Irradiance()
                            g_poa = irr_master.get_irradiance()
                            data[ctrl]['gpoa'] = g_poa
                            print_l(current_time(), "GPOA Irradiance for " + ctrl + ": " + str(g_poa))
                            # get the panel temperature using ambient temperature
                            amb_temp = w_read[1]
                            pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
                            data[ctrl]['temp'] = pan_temp
                            # get humidity data
                            data[ctrl]['humid'] = w_read[0]
                            '''PRE EDS ACTIVATION MEASUREMENT'''
                            # measure PRE EDS activation ocv and scc
                            ocv_pre = 0
                            scc_pre = 0
                            [ocv_pre, scc_pre] = test_master.run_measure_CTRL(panel_num)
                            print_l(current_time(), "PRE EDS OCV for " + ctrl + ": " + str(ocv_pre))
                            print_l(current_time(), "PRE EDS SCC for " + ctrl + ": " + str(scc_pre))
                            data[ctrl]['ocv_pre'] = ocv_pre
                            data[ctrl]['scc_pre'] = scc_pre
                            # compute the PRE EDS activation power measurements for each panel
                            power_pre = pow_master.get_power_out(ocv_pre, scc_pre, pan_temp)
                            print_l(current_time(), "PRE EDS Power for " + ctrl + ": " + str(power_pre))
                            data[ctrl]['pwr_pre'] = power_pre
                            # compute the PRE EDS activation PR measurements for each panel
                            pr_pre = pr_master.get_pr(ocv_pre, scc_pre, pan_temp, power_pre, g_poa)
                            print_l(current_time(), "PRE EDS PR for " + ctrl + ": " + str(pr_pre))
                            data[ctrl]['pr_pre'] = pr_pre
                            # compute the PRE EDS activation SI measurements for each panel
                            si_pre = soil_master.get_si(scc_pre, g_poa)
                            print_l(current_time(), "PRE EDS SI for " + ctrl + ": " + str(si_pre))
                            data[ctrl]['si_pre'] = si_pre

                            # NO EDS ACTIVATION AND POST MEASUREMENTS FOR CTRL PANELS
                            print_l(current_time(), "Not Activating EDS for " + ctrl + " panel")

                            # SAVE DATA TO USB
                            # write data to csv file
                            csv_master.write_data(data[ctrl])
                            print_l(current_time(), "Writing Results To CSV and TXT Files")
                            # delay before changing to next EDS panel
                            time.sleep(10)

                        # un-mount the usb drive
                        usb_master.reset_usb_mounts()
                        # turn of RED LED, indicating USB can be swapped
                        GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
                        GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
                        # time to swap USB if desired
                        time.sleep(10)
                    else:
                        print("Did not pass schedule and frequency checks")
        else:
            # Set Activation Flags to False in eds.json at the end of the day
            if json_reset:
                try:
                # load the json file
                    with open('/home/pi/Desktop/eds.json', 'r') as file:
                        json_file = json.load(file)
                    # reset all is_activated into false
                    eds_names = ['eds1', 'eds2', 'eds3', 'eds4', 'eds5']
                    for x in eds_names:
                        json_file[x].update({
                            'is_activated': False
                        })
                    # re-write the new json file
                    with open('/home/pi/Desktop/eds.json', 'w+') as file:
                        json.dump(json_file, file)
                except:
                    SM.ScheduleMaster.check_json_file(current_time())

        '''
        --------------------------------------------------------------------------
        BEGIN MANUAL ACTIVATION CODE
        The following code handles the manual activation of the specified EDS (in StaticManager.py) by flipping the switch
        Code outline:
        1) Check for changing input on switch pin
        2) If input is changed, and input is high (activate), then begin test
        '''
        input_state = GPIO.input(test_master.get_pin('inPinManualActivate'))
        if input_state == True:
            # mount the usb for data collection
            if usb_master.check_usb() == True:
                # mounts the usb
                usb_master.setup_usb_mount()
            else:
                print_l(current_time(), "No USB Detected!")
                usb_master.reset()
            # turn green and red LED on to show measuring time
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 1)
            # run EDS test on selected manual EDS
            eds_num = test_master.get_pin('manualEDSNumber')
            # get weather and time for data logging
            w_read = weather.read_humidity_temperature()

            # START SEQUENCE
            print_l(current_time(), "FORCED. Running Manual Activation Mode for EDS" + str(eds_num))
            # Get global irradiance data from pyranometer
            irr_master = SP420.Irradiance()
            g_poa = irr_master.get_irradiance()
            print_l(current_time(), "GPOA Measurement for EDS " + str(eds_num) + ": " + str(g_poa))
            # measure PV voc and isc before EDS activation
            [eds_ocv_before, eds_scc_before] = test_master.run_measure_EDS(eds_num)
            print_l(current_time(), "Pre-test OCV for EDS" + str(eds_num) + ": " + str(eds_ocv_before))
            print_l(current_time(), "Pre-test SCC for EDS" + str(eds_num) + ": " + str(eds_scc_before))
            # get the panel temperature using ambient temperature
            amb_temp = w_read[1]
            pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
            # compute the power measurements for each panel
            eds_power_before = pow_master.get_power_out(eds_ocv_before, eds_scc_before, pan_temp)
            print_l(current_time(),
                    "Pre-EDS Manual Activation Power Calculation for EDS" + str(eds_num) + ": " + str(eds_power_before))
            # compute the PR before eds activation
            eds_pr_before = pr_master.get_pr(eds_ocv_before, eds_scc_before, pan_temp, eds_power_before, g_poa)
            print_l(current_time(),
                    "Pre-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_before))
            # compute the SI before eds activation
            eds_si_before = soil_master.get_si(eds_scc_before, g_poa)
            print_l(current_time(),
                    "Pre-EDS Manual Activation SI Calculation for EDS" + str(eds_num) + ": " + str(eds_si_before))
            # activate the EDS film
            test_master.run_test(eds_num)
            # measure PV voc and isc after EDS activation
            [eds_ocv_after, eds_scc_after] = test_master.run_measure_EDS(eds_num)
            print_l(current_time(), "Post-EDS Manual Activation OCV for EDS" + str(eds_num) + ": " + str(eds_ocv_after))
            print_l(current_time(), "Post-EDS Manual Activation SCC for EDS" + str(eds_num) + ": " + str(eds_scc_after))
            # get the panel temperature using ambient temperature
            amb_temp = w_read[1]
            pan_temp = pow_master.get_panel_temp(amb_temp, g_poa)
            # compute the power measurements Post EDS
            eds_power_after = pow_master.get_power_out(eds_ocv_after, eds_scc_after, pan_temp)
            print_l(current_time(),
                    "Post-EDS Manual Activation Power for EDS" + str(eds_num) + ": " + str(eds_power_after))
            # compute the PR measurement Post EDS                       # compute the PR before eds activation
            eds_pr_after = pr_master.get_pr(eds_ocv_after, eds_scc_after, pan_temp, eds_power_after, g_poa)
            print_l(current_time(),
                    "Post-EDS Manual Activation PR Calculation for EDS" + str(eds_num) + ": " + str(eds_pr_after))
            # compute the SI before eds activation
            eds_si_after = soil_master.get_si(eds_scc_after, g_poa)
            print_l(current_time(),
                    "Post-EDS Manual Activation SI Calculation for EDS" + str(eds_num) + ": " + str(eds_si_after))
            # compile data
            man_power_data = [eds_power_before, eds_power_after]
            man_pr_data = [eds_pr_before, eds_pr_after]
            man_si_data = [eds_si_before, eds_si_after]

            # SAVE DATA TO USB
            # write data for EDS tested
            csv_master.write_manual_data(current_time(), w_read[1], w_read[0], g_poa, eds_num, eds_ocv_before, eds_ocv_after,
                                         eds_scc_before, eds_scc_after, man_power_data, man_pr_data, man_si_data)
            print_l(current_time(), "Writing Manual Testing Mode Measurements Results To CSV and TXT Files")
            # un-mount the usb drive
            usb_master.reset_usb_mounts()
            # turn of RED LED, indicating USB can be swapped
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)
            GPIO.output(test_master.get_pin('outPinLEDGreen'), 0)
            # time to swap USB if desired
            time.sleep(10)

            # FINISH
            print_l(current_time(), "Ended Manual Activation Test of EDS" + str(eds_num))

        '''
        END MANUAL ACTIVATION CODE
        --------------------------------------------------------------------------
        '''

        # remove error if corrected
        if "FATAL CORE ERROR" in error_list:
            error_list.remove("FATAL CORE ERROR")

    # END MASTER TRY-EXCEPT envelope
    except Exception as e:
        logging.exception("Bad error %s",e)
        add_error("FATAL CORE ERROR")
        raise

    # error handling
    if not not error_list:
        e_phrase = "Current error list: "
        for err in error_list:
            e_phrase += " [" + err + "]"
        print_l(current_time(), e_phrase)

    # blinking RED LED if error is raised
    if error_flag:
        if flip_on:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 1)
        else:
            GPIO.output(test_master.get_pin('outPinLEDRed'), 0)

            # END CORE LOOP
