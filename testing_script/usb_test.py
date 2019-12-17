import time
import os
import subprocess
import csv

USB_DIR_PATH = "/media/test/"

class USBMaster:
    def __init__(self):
        self.is_mounted = False
        self.USB_name = None
        self.USB_path = None
        self.set_USB_name()
        self.set_USB_path()
        #self.set_USB_path()

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
            self.USB_path = USB_DIR_PATH
    
    def process_sequence(self):
        # runs through necessary sequence for single method call
        self.set_USB_name()
        self.set_USB_path()

    def get_USB_path(self):
        # outputs USB file path
        return self.USB_path
    
    def get_USB_UUIDs(self):
        f=open("usb_names.txt", "r")
        if f.mode == 'r':
            usb_names = f.read().splitlines() 
            print(usb_names)
        f.close()

#Instantiate the usb class
usbmaster = USBMaster()

#Writing to USB Test

path = usbmaster.get_USB_path()+"usb_test.txt"
f = open(path, "a+")
f.write("Succesfully Writing File!\n")
f.close()

'''
#UUID setting
f=open("usb_names.txt", "r")
if f.mode == 'r':
    usb_names = f.read().splitlines() 
    print(usb_names)
f.close()

f = open("usb_setup.sh", "w+")
f.write("sudo mkdir /media/eds1\n")
f.write("sudo chown -R pi:pi /media/eds1\n")
f.write("sudo mount /dev/sda1 /media/eds1 -o uid=pi,gid=pi\n")
f.write("sudo umount /media/eds1\n")
f.close()

f=open("/etc/fstab", "w+)
f.write("UUID=18A9-9943 /media/usb vfat auto,nofail,noatime,users,rw,uid=pi,gid=pi 0 0")
'''

#Apply this link: https://www.raspberrypi-spy.co.uk/2014/05/how-to-mount-a-usb-flash-disk-on-the-raspberry-pi/
#sudo mkdir /media/usb
#sudo chown -R pi:pi /media/usb
#sudo mount /dev/sda1 /media/usb -o uid=pi,gid=pi
#umount /media/usb
#sudo nano /etc/fstab
#UUID=sample /media/usb vfat auto,nofail,noatime,users,rw,uid=pi,gid=pi 0 0

#Key Dependencies
#sudo apt-get install ntfs-3g
#sudo apt-get install exfat-fuse
#sudo apt-get install exfat-utils
#sudo apt-get install usbmount

#USB Format = FAT32