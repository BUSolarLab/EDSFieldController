#!/bin/bash
#
echo Initiating EDS Controller Setup...
echo ---
cd /home/pi/Desktop
echo ---
#
#echo Installing Python code from github.com/BUSolarLab/EDSFieldController...
#git clone https://github.com/BUSolarLab/EDSFieldController.git
#echo ---
#
echo Creating usb_names.txt on Desktop
touch usb_names.txt
echo ---
#
echo Installing external dependencies. THIS TAKES A MINUTE. PLEASE WAIT...
#uncomment if installing for rasbian lite (One must also create a Desktop directory for the pi)
#sudo apt-get install raspberrypi-ui-mods
#sudo apt-get install python3-pip
#python -m pip install --upgrade pip setuptools
#sudo apt-get install libatlas-base-dev
#sudo pip3 install numpy
sudo pip3 install RPI.GPIO
sudo pip3 install adafruit-circuitpython-pcf8523
pip3 install adafruit-circuitpython-mcp3xxx
sudo pip3 install adafruit-circuitpython-am2320
sudo pip3 install i2cdev
sudo apt-get update
sudo apt-get dist-upgrade
sudo apt-get upgrade
sudo apt-get install build-essential python-pip python-dev python-smbus git
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
cd Adafruit_Python_GPIO
sudo python3 setup.py install
git clone https://github.com/adafruit/Adafruit_CircuitPython_MCP3xxx
cd Adafruit_Python_MCP3xxx
sudo python3 setup.py install
echo ---
# usb mounting dependancies
echo Installing USB auto mount library and setting config...
sudo apt-get install mtools
sudo apt-get install ntfs-3g
sudo apt-get install exfat-fuse
sudo apt-get install exfat-utils
#do not need usb mount anymore do to errors with ntfs
#sudo apt-get install usbmount
sudo apt-get remove usbmount
sudo apt install nfs-kernel-server
# change config settings
sed -i "s/\(FS_MOUNTOPTIONS *= *\).*/\1\"-fstype=vfat,gid=users,dmask=0007,fmask=0117\"/" /etc/usbmount/usbmount.conf
sed -i "s/\(MountFlags *= *\).*/\1shared/" /lib/systemd/system/systemd-udevd.service
echo ---
#
echo Installing Watchdog timer and setting config...
modprobe bcm2835_wdt
echo "bcm2835_wdt" | tee -a /etc/modules
sudo apt-get install watchdog
sudo update-rc.d watchdog defaults
# uncomment line for running watchdog device
sed -i '/watchdog-device/s/^#//g' /etc/watchdog.conf
# add timeout line
sed -i '/watchdog-device/ a\watchdog-timeout = 15' /etc/watchdog.conf
# uncomment max load
sed -i '/max-load-1/s/^#//g' /etc/watchdog.conf
sed -i '/max-load-15/s/^#*/#/g' /etc/watchdog.conf
# uncomment interval
sed -i '/interval/s/^#//g' /etc/watchdog.conf
# start the watchdog
sudo service watchdog start
echo ---
#
echo INSTALLATION COMPLETE. THANK YOU FOR PLAYING.
