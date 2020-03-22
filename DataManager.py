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
HEADER_CSV = ["Date", "Time", "Temperature(C)", "Humidity(%)", "GPOA(W/M2)", "EDS/CTRL(#)", "Voc_Before(V)", "Voc_After(V)", "Isc_Before(A)", "Isc_After(A)", "Pout_Before(W)","Pout_After(W)", "PR_Before","PR_After", "SR_Before","SR_After"]
HEADER_TXT = "Date Time Temperature(C) Humidity(%) GPOA(W/M2) EDS/CTRL(#) Voc_Before(V) Voc_After(V) Isc_Before(A) Isc_After(A) Pout_Before(W) Pout_After(W) PR_Before PR_After SR_Before SR_After"

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
        print("Rebooting in 10 seconds...")
        time.sleep(10)
        subprocess.call("sudo reboot", shell=True)

    # setting the USB name by its UUID
    def set_USB_name(self):
        # check if USB mounted
        dir = str(subprocess.check_output("sudo blkid", shell=True))
        if "/dev/sda1:" in dir:
            self.label = dir.split('/dev/sda1:')[1].split('LABEL=')[1].split('"')[1]
            self.uuid = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
            print("Found USB named: "+self.uuid)
        else:
            print("USB not mounted! Please insert USB!")
            self.reset()

    # check if it is a new USB
    def check_new_USB(self):
        # get the uuid and labels from usb_names.txt
        f=open("/home/pi/Desktop/usb_names.txt", "r")
        usb_names = f.read().splitlines()
        f.close()
        # if empty list
        if not usb_names:
            print("Configurating new USB drive in FTU system!")
            f = open("/home/pi/Desktop/usb_names.txt", "a+")
            f.write(str(self.uuid)+" "+str(self.label)+"\n")
            f.close()
            self.set_USB_path()
            self.update_fstab_file()
            self.reset()
        # non empty list, already existing registered usbs
        else:
            # check if current usb is registered
            uuid_list = []
            label_list = []
            for x in usb_names:
                uuid_list.append(x.split()[0])
                label_list.append(x.split()[1])
            # current usb is registered
            if self.label in label_list:
                print("USB Already Registered!")
                self.set_USB_path()
            # current usb is not registered
            else:
                print("Configurating new USB drive in FTU system!")
                f = open("/home/pi/Desktop/usb_names.txt", "a+")
                f.write(str(self.uuid)+" "+str(self.label)+"\n")
                f.close()
                self.set_USB_path()
                self.update_fstab_file()
                self.reset()

    # set the USB path for data writing in MasterManager.py
    def set_USB_path(self):
        # gets USB file path for saving if USB name found
        if self.uuid is not None:
            self.USB_path = "/media/" + self.label

    # mount USB
    def setup_usb_mount(self):
        print("Mounting USB")
        # get current usb label
        dir = str(subprocess.check_output("sudo blkid", shell=True))
        cur_label = dir.split('/dev/sda1:')[1].split('LABEL=')[1].split('"')[1]
        cur_uuid = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
        # check if it is the same usb or not
        if self.label != cur_label:
            # reboot to reinitialize the usb, csv, and log classes
            print("Different USB Detected")
            self.reset()
        # mount the usb
        if not os.path.exists("/media/"+str(self.label)):
            subprocess.call("sudo mkdir /media/"+str(self.label), shell=True)
        subprocess.call("sudo chown -R pi:pi /media/"+str(self.label), shell=True)
        subprocess.call("sudo mount /dev/sda1 /media/"+str(self.label)+" -o uid=pi,gid=pi", shell=True)

    # un-mount all USBs
    def reset_usb_mounts(self):
        print("Un-Mounting USB")
        subprocess.call("sudo umount /media/"+str(self.label), shell=True)

    # edit fstab file to auto-mount when boot
    def update_fstab_file(self):
        print("Updating fstab file for new USB")
        # edit the stab file
        subprocess.call("sudo chown -R pi:pi /etc/fstab", shell=True)
        os.chmod("/etc/fstab", 0o777)
        f=open("/etc/fstab", "a+")
        f.write("UUID="+str(self.uuid)+" /media/"+str(self.label)+" vfat auto,nofail,noatime,users,permissions,rw,uid=pi,gid=pi 0 0\n")

    # check if there is a usb or not
    def check_usb(self):
        # check if USB mounted
        dir = str(subprocess.check_output("sudo blkid", shell=True))
        if "/dev/sda1:" in dir:
            return True
        else:
            return False
    
    # get the USB path
    def get_USB_path(self):
        # outputs USB file path
        return self.USB_path
    


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

        # new schedule locations
        self.csv_location = self.location_path + 'eds_data.csv'
        self.txt_location = self.location_path + 'eds_data.txt'

        # set up base csv and txt files if they don't exist
        self.check_empty_usb()
    
    # set up all initial csv and txt files if they don't exist
    def check_empty_usb(self):
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
                    f.writelines(HEADER_TXT + '\n')
            except:
                print("Error creating txt file! Please check.")
    
    def check_for_csv_file(self, name):
        if not os.path.isfile(name):
            try:
                with open(name, 'a+') as f:
                    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(HEADER_CSV)
            except:
                print("Error creating csv file! Please check.")
    
    # initialize folders and csv txt files for new schedule mode
    
    
    # construct object of data to be inserted in csv/txt file
    def data_row(self, data):
        # deconstruct the dictionary
        panel_name = data['name']
        dt = data['date_time']
        temp = data['temp']
        humid = data['humid']
        g_poa = data['gpoa']
        ocv_pre = data['ocv_pre']
        ocv_post = data['ocv_post']
        scc_pre = data['scc_pre']
        scc_post = data['scc_post']
        pwr_pre = data['pwr_pre']
        pwr_post = data['pwr_post']
        pr_pre = data['pr_pre']
        pr_post = data['pr_post']
        sr_pre = data['sr_pre']
        sr_post = data['sr_post']
        # create date and time 
        date = str(dt.tm_mon) + '/' + str(dt.tm_mday) + '/' + str(dt.tm_year)
        time = str(dt.tm_hour) + ':' + str(dt.tm_min) + ':' + str(dt.tm_sec)
        return [date, time, str(temp), str(humid), str(g_poa),panel_name, str(ocv_pre), str(ocv_post), str(scc_pre), str(scc_post), str(pwr_pre), str(pwr_post), str(pr_pre), str(pr_post), str(sr_pre), str(sr_post)]

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
    def write_csv_testing_data(self, data):
        row = self.data_row(data)
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
    def write_txt_testing_data(self, data):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row(data)
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
    def write_csv_noon_data(self, data):
        # self, dt, temp, humid, g_poa, eds_act, eds_ctrl_num, volt, cur, power, pr, sr
        row = self.data_row(data)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_noon_data, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv solar noon testing data!")
    
    # write to txt version of solar noon testing data log file
    def write_txt_noon_data(self, data):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row(data)
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
    def write_testing_data(self, data):
        self.write_txt_testing_data(data)
        self.write_csv_testing_data(data)
        
    # write to noon data files
    def write_noon_data(self, data):
        self.write_txt_noon_data(data)
        self.write_csv_noon_data(data)
    
    # write to manual data files
    def write_manual_data(self, dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data):
        self.write_txt_manual_data(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data)
        self.write_csv_manual_data(dt, temp, humid, g_poa, eds_num, eds_ocv_before, eds_ocv_after, eds_scc_before, eds_scc_after, eds_power, pr_data, sr_data)
    
    
    # write data to designated panel folder
    def write_data(self, data):
        # write the txt file
        self.write_txt_data(data)
        # write the csv file
        self.write_csv_data(data)
    
    # write to txt version of EDS testing data log file (two copies of data for fidelity)
    def write_txt_data(self, data):
        # process raw data into txt dump format with space delimiters
        row_raw = self.data_row(data)
        print("TXT: ", row_raw)
        row = ""
        for param in row_raw:
            row += param
            row += " "
        row += '\n'
        
        try:
            with open(self.txt_location, 'a') as f_txt:
                f_txt.writelines(row)
        except:
            print("Error writing txt EDS data!")
    
    # write to csv version of EDS testing data log file
    def write_csv_data(self, data):
        row = self.data_row(data)
        print("CSV: ", row)
        try:
            # attempt to open csv file in append mode (don't want to create lots of files)
            with open(self.csv_location, mode='a') as f_csv:
                # write data to csv file
                writer = csv.writer(f_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(row)
        except:
            print("Error writing csv EDS data!")
        
            
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
            with open(self.log_file, 'a+') as f_log:
                f_log.writelines(datetime + ' - ' + phrase + '\n')
        except:
            print("Error writing to existing log file! Please check.")


'''
The following function calculates precise solar noon time dependent on given time zone and latitude.
This will allow testing schedules to coordinate around local solar noon.
'''
   
def get_solar_time(gmt_off, longitude, dt):
    # implementation adapted from https://sciencing.com/calculate-solar-time-8612288.html
    A = 15 * gmt_off
    B = (dt.tm_yday - 81) * 360 / 365
    C = 9.87 * sin(deg2rad(2 * B)) - 7.53 * cos(deg2rad(B)) - 1.58 * sin(deg2rad(B))
    D = 4 * (A - longitude) + C
    # return solar time offset in minutes
    return D