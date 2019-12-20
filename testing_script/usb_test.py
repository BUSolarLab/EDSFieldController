import time
import os
import subprocess
import csv

USB_DIR_PATH = "/media/redusb/"

class USBMaster:
    def __init__(self):
        self.USB_name = None
        self.USB_path = None
        self.uuid = None
        self.set_USB_name()
        self.set_USB_path()

    def reset(self):
        # resets parameters if needed
        #self.__init__()
        subprocess.call("sudo reboot", shell=True)

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
            #self.USB_path = USB_DIR_PATH
            uuid_dict = {}
            try:
                f=open("/home/pi/Desktop/EDSFieldController/testing_script/usb_names.txt", "r")
                if f.mode == 'r':
                    usb_names = f.read().splitlines() 
                f.close()
                for x in usb_names:
                    uuid = x.split()[0]
                    usb_mount = x.split()[1]
                    uuid_dict[uuid] = usb_mount
                self.USB_path = "/media/" + uuid_dict[self.USB_name]
                self.uuid = uuid_dict[self.USB_name]
            except:
                # get associated variables
                dir = str(subprocess.check_output("sudo blkid", shell=True))
                label = dir.split('/dev/sda1:')[1].split('LABEL_FATBOOT=')[1].split('"')[1]
                uuid = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
                f = open("/home/pi/Desktop/EDSFieldController/testing_script/usb_names.txt", "a+")
                f.write("\n"+str(uuid)+" "+str(label))
                f.close()
                self.set_mounting_port()

    def set_mounting_port(self):
        # get associated variables
        dir = str(subprocess.check_output("sudo blkid", shell=True))
        label = dir.split('/dev/sda1:')[1].split('LABEL_FATBOOT=')[1].split('"')[1]
        uuid = dir.split('/dev/sda1:')[1].split('UUID=')[1].split('"')[1]
        # setup the bash script
        f = open("/home/pi/Desktop/EDSFieldController/testing_script/usb_setup.sh", "w+")
        f.write("sudo mkdir /media/"+str(label)+"\n")
        f.write("sudo chown -R pi:pi /media/"+str(label)+"\n")
        f.write("sudo mount /dev/sda1 /media/"+str(label)+" -o uid=pi,gid=pi\n")
        #f.write("sudo umount /media/"+str(label)+"\n")
        f.close()
        # edit the stab file
        subprocess.call("sudo chown -R pi:pi /etc/fstab", shell=True)
        os.chmod("/etc/fstab", 0o777)
        f=open("/etc/fstab", "a+")
        f.write("UUID="+str(uuid)+" /media/"+str(label)+" vfat auto,nofail,noatime,users,rw,uid=pi,gid=pi 0 0")
        # reboot
        #self.reset()

    def get_USB_path(self):
        # outputs USB file path
        return self.USB_path
    
    def get_USB_UUID(self):
        # outputs USB UUID
        return self.uuid
    

#Instantiate the usb class
usbmaster = USBMaster()

#Writing to USB Test
path = "/media/pi/JES/usb_test.txt"
f = open(path, "a+")
f.write("Succesfully Writing File!\n")
f.close()


#UUID setting
'''
uuid_dict = {}
f=open("usb_names.txt", "r")
if f.mode == 'r':
    usb_names = f.read().splitlines() 
    print(usb_names)
f.close()
for x in usb_names:
    uuid = x.split()[0]
    usb_mount = x.split()[1]
    uuid_dict[uuid] = usb_mount
print(uuid_dict)
'''
#Setting up mount
'''
f = open("usb_setup.sh", "w+")
f.write("sudo mkdir /media/eds1\n")
f.write("sudo chown -R pi:pi /media/eds1\n")
f.write("sudo mount /dev/sda1 /media/eds1 -o uid=pi,gid=pi\n")
f.write("sudo umount /media/eds1\n")
f.close()

f=open("/etc/fstab", "w+)
f.write("UUID=18A9-9943 /media/usb vfat auto,nofail,noatime,users,rw,uid=pi,gid=pi 0 0")
'''
#---------------------------------------------------------------------------------------------------
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



'''
def process_sequence(self):
    # runs through necessary sequence for single method call
    self.set_USB_name()
    self.set_USB_path()
'''