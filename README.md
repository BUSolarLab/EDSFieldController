# EDSFieldController

> I will update this with more detail shortly.

Please follow these steps to set up a brand new Raspberry Pi 3 B+

1. Download and install Raspbian
2. Download and run eds_setup.sh using 'chmod +x eds_setup.sh' then 'sudo ./eds_setup.sh' (you will have to type 'y' as a prompt at some point during the installation)
3. Enable SPI and I2C
4. Reboot system 'sudo reboot'
5. Open MasterManager.py and uncomment line 60, filling in the appropriate time variables for the eventual location of test unit (this initiates the RTC for a certain time that it will maintain)
6. Run MasterManager.py once to make sure everything works
7. Recomment line 60 so that it does not reset time again
8. Change config.json file to location and setup specifications
9. Add the following line above 'exit 0' in /etc/rc.local (must use root access to edit file 'sudo nano /etc/rc.local')
10. RPi is now ready for automated function
