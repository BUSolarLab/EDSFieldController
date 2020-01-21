'''
=============================
Title: USB and Data Writing - EDS Field Control
Author: Benjamin Considine, Brian Mahabir, Aditya Wikara
Started: September 2018
=============================
'''
import time
import os
import subprocess
import csv
from math import cos, sin
from numpy import deg2rad

# necessary constants
DATA_HEADER_CSV = ["Date", "Time", "Temperature(C)", "Humidity(%)", "GPOA(W/M2)","EDS(#)", "OCV_Before(V)", "OCV_After(V)", "SCC_Before(A)", "SCC_After(A)", "CTRL1_OCV(V)", "CTRL1_SCC(A)", "CTRL2_OCV(V)", "CTRL2_SCC(A)", "EDS_PWR_Before(W)", "EDS_PWR_After(W)", "CTRL1_PWR(W)","CTRL2_PWR(W)"]
DATA_HEADER_TXT = "Date Time Temperature(C) Humidity(%) GPOA(W/M2) EDS(#) OCV_Before(V) OCV_After(V) SCC_Before(A) SCC_After(A) CTRL1_OCV(V) CTRL1_SCC(A) CTRL2_OCV(V) CTRL2_SCC(A) EDS_PWR_Before(W) EDS_PWR_After(W) CTRL1_PWR(W) CTRL2_PWR(W)"

NOON_HEADER_CSV = ["Date", "Time", "Temperature(C)", "Humidity(%)", "GPOA(W/M2)", "PRE/POST","EDS/CTRL(#)", "OCV(V)", "SCC(A)", "Power(W)", "PR", "SR"]
NOON_HEADER_TXT = "Date Time Temperature(C) Humidity(%) GPOA(W/M2) PRE/POST EDS/CTRL(#) OCV(V) SCC(A) Power(W) PR SR"

MANUAL_HEADER_CSV = ["Date", "Time", "Temperature(C)", "Humidity(%)", "GPOA(W/M2)","EDS(#)", "OCV_Before(V)", "OCV_After(V)", "SCC_Before(A)", "SCC_After(A)", "EDS_PWR_Before(W)","EDS_PWR_After(W)","EDS_PR_Before", "EDS_PR_After", "EDS_SR_Before", "EDS_SR_After"]
MANUAL_HEADER_TXT = "Date Time Temperature(C) Humidity(%) GPOA(W/M2) EDS(#) OCV_Before(V) OCV_After(V) SCC_Before(A) SCC_After(A) EDS_PWR_Before(W) EDS_PWR_After(W) EDS_PR_BEFORE EDS_PR_AFTER EDS_SR_BEFORE EDS_SR_AFTER"

'''
USB Master Class:
Functionality:
1) Checks if USB is mounted
2) If mounted, gets USB label and uuid
3) Sets the USB path for data writing
'''

class USBMaster:
    def __init__(self):
        self.USB_name = None
        self.USB_path = None
        self.uuid = None
        self.label = None
        self.set_USB_name()
        self.check_new_USB()

    # reset function, basically reboots the system through command line
    def reset(self):
        subprocess.call("sudo reboot", shell=True)

    # setting the USB name by its UUID
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
    
    # check if it is a new USB
    def check_new_USB(self):
        # set label and uuid
        dir = str(subprocess.check_output("sudo blkid", shell=True))
        self.label = dir.split('/dev/sda1:')[1].split('LABEL=')[1].split('"')[1]
        self.uuid = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
        # get the uuid and labels from usb_names.txt
        f=open("/home/pi/Desktop/EDSFieldController/usb_names.txt", "r")
        usb_names = f.read().splitlines() 
        f.close()
        # put them in a seperate list
        uuid_list = []
        label_list = []
        for x in usb_names:
            uuid_list.append(x.split()[0])
            label_list.append(x.split()[1])
        # cross check label and uuid with usb_names.txt
        if self.label in label_list:
            print("USB Already Registered!")
            self.set_USB_path()
            #self.set_mounting_port()
        else:
            print("Configurating new USB drive in FTU system!")
            f = open("/home/pi/Desktop/EDSFieldController/usb_names.txt", "a+")
            f.write(str(self.uuid)+" "+str(self.label)+"\n")
            f.close()
            self.set_USB_path()
            self.set_mounting_port()

    # set the USB path for data writing in MasterManager.py
    def set_USB_path(self):
        # gets USB file path for saving if USB name found
        if self.USB_name is not None:
            self.USB_path = "/media/" + self.label

    # if new USB, need to mount it and configure new UUID in fstab file
    def set_mounting_port(self):
        # setup the bash script
        f = open("/home/pi/Desktop/EDSFieldController/usb_setup.sh", "w+")
        f.write("sudo mkdir /media/"+str(self.label)+"\n")
        f.write("sudo chown -R pi:pi /media/"+str(self.label)+"\n")
        f.write("sudo mount /dev/sda1 /media/"+str(self.label)+" -o uid=pi,gid=pi\n")
        #f.write("sudo umount /media/"+str(label)+"\n")
        f.close()
        #Run the bash script
        subprocess.call("chmod +x /home/pi/Desktop/EDSFieldController/usb_setup.sh", shell=True)
        subprocess.call("./usb_setup.sh", shell=True)
        # edit the stab file
        subprocess.call("sudo chown -R pi:pi /etc/fstab", shell=True)
        os.chmod("/etc/fstab", 0o777)
        f=open("/etc/fstab", "a+")
        f.write("UUID="+str(self.uuid)+" /media/"+str(self.label)+" vfat auto,nofail,noatime,users,rw,uid=pi,gid=pi 0 0")

    def get_USB_path(self):
        # outputs USB file path
        return self.USB_path
    
    def get_USB_UUID(self):
        # outputs USB UUID
        return self.uuid


'''
CSV Master Class:
Functionality:
1) Checks if txt and csv files exit, creates them if not
2) Has methods for writing data to csv files
'''

class CSVMaster:
    # initialize all file names to write to
    def __init__(self, usb_path):
        self.location_path = usb_path + '/'
        self.txt_testing_data = self.location_path + 'testing_data.txt'
        self.csv_testing_data = self.location_path + 'testing_data.csv'
        self.txt_noon_data = self.location_path + 'noon_data.txt'
        self.csv_noon_data = self.location_path + 'noon_data.csv'
        self.txt_manual_data = self.location_path + 'manual_data.txt'
        self.csv_manual_data = self.location_path + 'manual_data.csv'

        # set up base csv and txt files if they don't exist
        self.check_for_txt_file(self.txt_testing_data)
        self.check_for_txt_file(self.txt_noon_data)
        self.check_for_txt_file(self.txt_manual_data)
        self.check_for_csv_file(self.csv_testing_data)
        self.check_for_csv_file(self.csv_noon_data)
        self.check_for_csv_file(self.csv_manual_data)

    # checks for existing data file, and creates it if none exist
    def check_for_txt_file(self, name):
        if not os.path.isfile(name):
            try:
                with open(name, 'a+') as f:
                    if name is self.txt_testing_data:
                        f.writelines(DATA_HEADER_TXT + '\n')
                    if name is self.txt_noon_data:
                        f.writelines(NOON_HEADER_TXT + '\n')
                    if name is self.txt_manual_data:
                        f.writelines(MANUAL_HEADER_TXT + '\n')
            except:
                print("Error creating txt file! Please check.")
    
    def check_for_csv_file(self, name):
        if not os.path.isfile(name):
            try:
                with open(name, 'a+') as f:
                    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    if name is self.csv_testing_data:
                        writer.writerow(DATA_HEADER_CSV)
                    if name is self.csv_noon_data:
                        writer.writerow(NOON_HEADER_CSV)
                    if name is self.csv_manual_data:
                        writer.writerow(MANUAL_HEADER_CSV)
            except:
                print("Error creating csv file! Please check.")
        
    
    # construct data object with all the necessary parameters
    def data_row_test(self, dt, temp, humid, g_poa, eds_num, params, power):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        time = str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
        out = [date, time, str(temp), str(humid), str(g_poa), str(eds_num)]
        #Append the voc and isc measurement results from the control panels
        for par in params:
            out.append(str(par))
        #Append the Power results 
        for i in power:
            out.append(str(i))
        return out

    def data_row_noon(self, dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        time = str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
        return [date, time, str(temp), str(humid), str(g_poa), str(eds_act),str(eds_ctrl_num), str(volt), str(cur), str(power), str(pr), str(sr)]

    def data_row_manual(self, dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data):
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        time = str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
        out = [date, time, str(temp), str(humid), str(g_poa), str(eds_num), str(eds_ocv_before), str(eds_ocv_after), str(eds_scc_before), str(eds_scc_after)]
        #Append power data
        for x in eds_power:
            out.append(str(x))
        #Append PR data
        for x in pr_data:
            out.append(str(x))
        #Append SR data
        for x in sr_data:
            out.append(str(x))

        return out
    
    # write to csv version of EDS testing data log file
    def write_csv_testing_data(self, dt, temp, humid, g_poa, eds_num, params, power):
        row = self.data_row_test(dt, temp, humid, g_poa, eds_num, params, power)
        print("CSV: ", row)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_testing_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv EDS testing data!")
        
    
    # write to txt version of EDS testing data log file (two copies of data for fidelity)
    def write_txt_testing_data(self, dt, temp, humid, g_poa, eds_num, params, power):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row_test(dt, temp, humid, g_poa, eds_num, params, power)
        print("TXT: ", row_raw)
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
    def write_csv_noon_data(self, dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr):
        row = self.data_row_noon(dt, temp, humid, g_poa, eds_act, eds_ctrl_num, b_volt, volt, cur, power, pr, sr)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_noon_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv solar noon testing data!")
    
    # write to txt version of solar noon testing data log file
    def write_txt_noon_data(self, dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row_noon(dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr)
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
    
    # write to csv version of manual testing data log file
    def write_csv_manual_data(self, dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power,pr_data,sr_data):
        row = self.data_row_manual(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power,pr_data,sr_data)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_manual_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv manual testing data!")
    
    # write to txt version of manual  testing data log file
    def write_txt_manual_data(self, dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row_manual(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data)
        row = ""
        for param in row_raw:
            row += param
            row += " "
        row += '\n'
        
        try:
            with open(self.txt_manual_data, 'a+') as f_txt:
                f_txt.writelines(row)
        except:
            print("Error writing txt manual data!")
            
    # write to testing data files
    def write_testing_data(self, dt, temp, humid, g_poa, eds_num, params, power):
        self.write_txt_testing_data(dt, temp, humid, g_poa, eds_num, params, power)
        self.write_csv_testing_data(dt, temp, humid, g_poa, eds_num, params, power)
        
    # write to noon data files
    def write_noon_data(self, dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr):
        self.write_txt_noon_data(dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr)
        self.write_csv_noon_data(dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr)
    
    # write to manual data files
    def write_manual_data(self, dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data):
        self.write_txt_manual_data(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data)
        self.write_csv_manual_data(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data)
            
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
    C = 9.87 * sin(deg2rad(2 * B)) - 7.53 * cos(deg2rad(B)) - 1.58 * sin(deg2rad(B))
    D = 4 * (A - longitude) + C
    # return solar time offset in minutes
    return D

