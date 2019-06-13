# EDSFieldController

> I will update this with more detail shortly.

Please follow these steps to set up a brand new Raspberry Pi 3 B+

1. Download and install Raspbian
2. Download and run eds_setup.sh using 'chmod +x eds_setup.sh' then 'sudo ./eds_setup.sh' (you will have to type 'y' as a prompt at some point during the installation)
3. Enable SPI and I2C
4. Reboot system 'sudo reboot'
5. Run MasterManager.py to make sure everything works
6. Change config.json file to location and setup specifications
7. Add the following line above 'exit 0' in /etc/rc.local (must use root access to edit file 'sudo nano /etc/rc.local')
8. RPi is now ready for automated function
