'''
This is central control.
This file contains the main looping structure for extended-period field testing.
'''

import RPi.GPIO as GPIO
import time


import StaticManager as SM
import DataManager as DM
import RebootManager as RM
import TestingManager as TM

# master setup
GPIO.setmode(GPIO.BOARD)


# read config, get constants, etc
print("Initializing...")
static_master = SM.StaticMaster()
USB_master = DM.USBMaster()
test_master = TM.TestingMaster(static_master.get_config())


'''
~~~CORE LOOP~~~
This loop governs the overall code for the long term remote testing of the field units
1) Checks the time of day
2) Checks the temperature and humidity before testing
3) Runs testing sequence
4) Writes data to log files
5) Alerts in the case of an error
'''

stopped = False
while not stopped:
    # update time of day by getting data from RTC
    # 1) Check if RTC exists
    # 2) If yes, get time data
    
    
    # Check for errors (?)
    # If everything okay, flip green LED output (this will cause LED to blink 1 sec on, 1 sec off
    # If errors found, halt program and flash red LED
    
    
    # check time against prescribed testing times for each EDS
    # 1) If within 5 seconds of testing time for EDS, initiate testing sequence

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # delay to slow down processing
    time.sleep(1)
    
    
    

