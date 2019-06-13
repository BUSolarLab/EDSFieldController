#!/bin/bash
#
echo Initiating EDS Controller Setup...
echo ---
echo Creating EDSPython folder
mkdir -m 777 /home/pi/EDSPython
cd /home/pi/EDSPython
echo ---
#
echo Installing Python code from github.com/BUSolarLab/EDSFieldController...
git clone https://github.com/BUSolarLab/EDSFieldController.git
cp /home/pi/EDSPython/EDSFieldController/AM2315.py /home/pi/EDSPython
cp /home/pi/EDSPython/EDSFieldController/DataManager.py /home/pi/EDSPython
cp /home/pi/EDSPython/EDSFieldController/MasterManager.py /home/pi/EDSPython
cp /home/pi/EDSPython/EDSFieldController/StaticManager.py /home/pi/EDSPython
cp /home/pi/EDSPython/EDSFieldController/TestingManager.py /home/pi/EDSPython
cp /home/pi/EDSPython/EDSFieldController/config.json /home/pi/EDSPython
echo ---
#
echo Installing external dependencies. THIS TAKES A MINUTE. PLEASE WAIT...
pip3 install RPI.GPIO
pip3 install adafruit-circuitpython-pcf8523
apt-get update
apt-get install build-essential python-pip python-dev python-smbus git
git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
cd Adafruit_Python_GPIO
python setup.py install
git clone https://github.com/adafruit/Adafruit_Python_MCP3008.git
cd Adafruit_Python_MCP3008
python setup.py install
echo ---
#
echo Moving files around...
cp -r /home/pi/.local/lib/p*/s*/adafruit_register /home/pi/EDSPython
cp /home/pi/.local/lib/p*/s*/adafruit_pcf8523.py /home/pi/EDSPython
cp -r /home/pi/EDSPython/Adafruit_Python_GPIO/Adafruit_Python_MCP3008 /home
cp -r /home/Adafruit_Python_MCP3008/Adafruit_MCP3008 /home/pi/EDSPython
cp -r /home/Adafruit_Python_GPIO/Adafruit_GPIO /home/pi/EDSPython
echo ---
#
echo Installing USB auto mount library and setting config...
apt-get install usbmount
# change config settings
sed -i "s/\(FS_MOUNTOPTIONS *= *\).*/\1\"-fstype=vfat,gid=users,dmask=0007,fmask=0117\"/" /etc/usbmount/usbmount.conf
sed -i "s/\(MountFlags *= *\).*/\1shared/" /lib/systemd/system/systemd-udevd.service
echo ---
#
echo Installing Watchdog timer and setting config...
modprobe bcm2835_wdt
echo "bcm2835_wdt" | tee -a /etc/modules
apt-get install watchdog
update-rc.d watchdog defaults
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
service watchdog start
echo ---
#
echo INSTALLATION COMPLETE. THANK YOU FOR PLAYING.
echo Now please follow the rest of the steps to set up this Raspberry Pi.
echo Cheers,      
echo    Ben Considine
