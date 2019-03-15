'''
NOTE - Sections of this code are taken from Adafruit at:
https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/script
'''

import time
import os
import subprocess
import busio
import digitalio
import board
import csv
from math import cos, sin

# necessary constants
USB_DIR_PATH = "/media/pi/"
DATA_HEADER_CSV = ["Date", "Time", "Temperature(C)", "Humidity(%)", "EDS(#)", "SCC_Before(amps)", "SCC_After(amps)"]
DATA_HEADER_TXT = "Date Time Temperature(C) Humidity(%) EDS(#) SCC_Before(amps) SCC_After(amps)"


'''
USB Master Class:
Functionality:
1) Checks if USB is mounted
2) If mounted, gets USB name
3) If USB name found, construct file path for saving files to USB
'''


class USBMaster:
    def __init__(self):
        self.USB_name = None
        self.USB_path = None
        self.is_mounted = False
        self.set_USB_name()
        self.set_USB_path()

    def reset(self):
        # resets parameters if needed
        self.__init__()

    def set_USB_name(self):
        # check if USB mounted
        try:
            dir = str(subprocess.check_output("sudo blkid", shell=True))
            if "/dev/sda1:" in dir:
                self.USB_name = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
                print("Found USB named: "+self.USB_name)
            else:
                self.reset()
                print("USB not mounted! Please insert USB.")

        except:
            self.reset()
            print("ERROR: Shell process malfunction!")

    def set_USB_path(self):
        # gets USB file path for saving if USB name found
        if self.USB_name is not None:
            self.USB_path = USB_DIR_PATH+self.USB_name
            
    def process_sequence(self):
        # runs through necessary sequence for single method call
        self.set_USB_name()
        self.set_USB_path()

    def get_USB_path(self):
        # outputs USB file path
        return self.USB_path


'''
CSV Master Class:
Functionality:
1) Checks if txt and csv files exit, creates them if not
2) Has methods for writing data to files
'''


class CSVMaster:
    # initialize all file names to write to
    def __init__(self, usb_path):
        self.location_path = usb_path + '/'
        self.txt_testing_data = self.location_path + 'testing_data.txt'
        self.csv_testing_data = self.location_path + 'testing_data.csv'
        self.txt_noon_data = self.location_path + 'noon_data.txt'
        self.csv_noon_data = self.location_path + 'noon_data.csv'
        
        # set up base csv and txt files if they don't exist
        self.check_for_txt_file(self.txt_testing_data)
        self.check_for_txt_file(self.txt_noon_data)
        self.check_for_csv_file(self.csv_testing_data)
        self.check_for_csv_file(self.csv_noon_data)
        
    
    # checks for existing data file, and creates it if none exist
    def check_for_txt_file(self, name):
        if not os.path.isfile(name):
            try:
                with open(name, 'a') as f:
                    f.writelines(DATA_HEADER_TXT + '\n')
            except:
                print("Error creating txt file! Please check.")
    
    def check_for_csv_file(self, name):
        if not os.path.isfile(name):
            try:
                with open(name, 'a') as f:
                    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(DATA_HEADER_CSV)
            except:
                print("Error creating csv file! Please check.")
        
    
    # construct data object with all the necessary parameters
    def data_row(self, dt, temp, humid, eds_num, b_cur, a_cur):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        time = str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
        return [date, time, str(temp), str(humid), str(eds_num), str(b_cur), str(a_cur)]
    
    
    # write to csv version of EDS testing data log file
    def write_csv_testing_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        row = self.data_row(dt, temp, humid, eds_num, b_cur, a_cur)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_testing_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv EDS testing data!")
        
    
    # write to txt version of EDS testing data log file (two copies of data for fidelity)
    def write_txt_testing_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row(dt, temp, humid, eds_num, b_cur, a_cur)
        row = ""
        for param in row_raw:
            row += param
            row += " "
        row += '\n'
        
        try:
            with open(self.txt_testing_data, 'a') as f_txt:
                f_txt.writelines(row)
        except:
            print("Error writing txt EDS testing data!")
    
    
    # write to csv version of solar noon testing data log file
    def write_csv_noon_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        row = self.data_row(dt, temp, humid, eds_num, b_cur, a_cur)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_noon_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv solar noon testing data!")    
    
    
    # write to txt version of solar noon testing data log file
    def write_txt_noon_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row(dt, temp, humid, eds_num, b_cur, a_cur)
        row = ""
        for param in row_raw:
            row += param
            row += " "
        row += '\n'
        
        try:
            with open(self.txt_noon_data, 'a') as f_txt:
                f_txt.writelines(row)
        except:
            print("Error writing txt solar noon data!")
            
    
    # write to testing data files
    def write_testing_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        self.write_txt_testing_data(self, dt, temp, humid, eds_num, b_cur, a_cur)
        self.write_csv_testing_data(self, dt, temp, humid, eds_num, b_cur, a_cur)
        
    # write to noon data files
    def write_noon_data(self, dt, temp, humid, eds_num, b_cur, a_cur):
        self.write_txt_noon_data(self, dt, temp, humid, eds_num, b_cur, a_cur)
        self.write_csv_noon_data(self, dt, temp, humid, eds_num, b_cur, a_cur)
            
'''
Log Master Class:
Functionality:
1) Checks if log file exists, creates it if not
2) Has method for writing to log file with current date/time
'''            
            
            
class LogMaster:
    # initialize log file name to write to
    def __init__(self, usb_path, dt):
        self.location_path = usb_path + '/'
        self.log_file = self.location_path + 'log.txt'
        self.date_created = dt
        
        # set up base csv and txt files if they don't exist
        self.check_for_log_file(self.date_created)
        
    
    # checks for existing log file, and creates it if none exist
    def check_for_log_file(self, dt):
        if not os.path.isfile(self.log_file):
            datetime = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
            try:
                with open(self.log_file, 'a') as f:
                    f.writelines("Log File of Field Unit Activity. Created on: " + datetime + '\n')
            except:
                print("Error creating log file! Please check.")
                
    
    # write phrase to log file
    def write_log(self, dt, phrase):
        try:
            # create datetime phrase to log data
            datetime = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year) + ' ' + str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
            with open(self.log_file, 'a') as f_log:
                f_log.writelines(datetime + ' - ' + phrase + '\n')
        except:
            print("Error writing to existing log file! Please check.")

                         
                         
    
'''
The following function calculates precise solar noon time dependent on given time zone and latitude.
This will allow testing schedules to coordinate around local solar noon.
'''
   
   
def get_solar_time(gmt_off, dt, longitude, latitude):
    # implementation adapted from https://sciencing.com/calculate-solar-time-8612288.html
    A = 15 * gmt_off
    B = (dt.tm_yday - 81) * 360 / 365
    C = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.58 * sin(B)
    D = 4 * (A - longitude) + C
    
    # return solar time offset in minutes
    return D


        
        
