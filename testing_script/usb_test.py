import time
import os
import subprocess
import csv

USB_DIR_PATH = "/media/usb/"

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


usbmaster = USBMaster()
path = usbmaster.get_USB_path()+"usb_test.txt"
f = open(path, "a+")
f.write("Succesfully Writing File!")
f.close()

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